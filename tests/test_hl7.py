import unittest

from clinkit.hl7 import DEFAULT_DELIMITERS, Delimiters, Hl7Error, Message, Segment, escape_text, unescape_text

RAW = (
    "MSH|^~\\&|LIS|MAIN|CLINKIT|MAIN|20250303090000||ORU^R01|MSG001|P|2.5\r"
    "PID|1||MRN00000018||Testson^Pat~Alias^P||19800615|F\r"
    "OBR|1|LO3-000001||K^Potassium\r"
    "OBX|1|NM|K^Potassium||4.2|mmol/L|3.5-5.1|N\r"
)


class DelimiterTests(unittest.TestCase):
    def test_from_msh(self):
        d = Delimiters.from_msh("MSH#*+!$#rest")
        self.assertEqual((d.field, d.component, d.repeat, d.escape, d.sub), ("#", "*", "+", "!", "$"))

    def test_rejects_duplicate_characters(self):
        with self.assertRaises(Hl7Error):
            Delimiters(field="|", component="|")

    def test_requires_msh(self):
        with self.assertRaises(Hl7Error):
            Delimiters.from_msh("PID|1")


class EscapeTests(unittest.TestCase):
    def test_round_trip(self):
        text = "a|b^c~d&e\\f"
        self.assertEqual(unescape_text(escape_text(text)), text)

    def test_named_sequences(self):
        self.assertEqual(unescape_text("x\\F\\y\\S\\z\\T\\w\\R\\v\\E\\"), "x|y^z&w~v\\")

    def test_line_break_and_hex(self):
        self.assertEqual(unescape_text("a\\.br\\b"), "a\nb")
        self.assertEqual(unescape_text("\\X41\\\\X4A4B\\"), "AJK")

    def test_formatting_sequences_are_dropped(self):
        self.assertEqual(unescape_text("\\H\\bold\\N\\ text"), "bold text")

    def test_unterminated_sequence_raises(self):
        with self.assertRaises(Hl7Error):
            unescape_text("abc\\Fdef")

    def test_bad_hex_raises(self):
        with self.assertRaises(Hl7Error):
            unescape_text("\\XZZ\\")


class SegmentTests(unittest.TestCase):
    def test_msh_numbering(self):
        msh = Segment.parse("MSH|^~\\&|LIS|MAIN", DEFAULT_DELIMITERS)
        self.assertEqual(msh.value(1), "|")
        self.assertEqual(msh.value(2), "^~\\&")
        self.assertEqual(msh.value(3), "LIS")
        self.assertEqual(msh.value(4), "MAIN")

    def test_components_and_subcomponents(self):
        seg = Segment.parse("PID|1||ID1^^^HOSP&NORTH&L||Doe^Jan", DEFAULT_DELIMITERS)
        self.assertEqual(seg.value(3, 1), "ID1")
        self.assertEqual(seg.value(3, 4, sub=2), "NORTH")
        self.assertEqual(seg.components(5), ["Doe", "Jan"])

    def test_repetitions(self):
        seg = Segment.parse("PID|1||X||A^B~C^D", DEFAULT_DELIMITERS)
        self.assertEqual(seg.value(5, 1, rep=2), "C")
        self.assertEqual(len(seg.repetitions(5)), 2)
        self.assertEqual(seg.value(5, 1, rep=3), "")

    def test_missing_fields_are_empty(self):
        seg = Segment.parse("OBR|1", DEFAULT_DELIMITERS)
        self.assertEqual(seg.value(9), "")
        self.assertEqual(seg.components(9), [])

    def test_escaped_data_is_decoded_on_read(self):
        seg = Segment.parse("NTE|1||pressure 120\\S\\80\\F\\ok", DEFAULT_DELIMITERS)
        self.assertEqual(seg.value(3), "pressure 120^80|ok")

    def test_bad_segment_name(self):
        with self.assertRaises(Hl7Error):
            Segment.parse("x|1", DEFAULT_DELIMITERS)


class MessageTests(unittest.TestCase):
    def test_parse_basic(self):
        msg = Message.parse(RAW)
        self.assertEqual([s.name for s in msg.segments], ["MSH", "PID", "OBR", "OBX"])
        self.assertEqual(msg.message_type, "ORU^R01")
        self.assertEqual(msg.control_id, "MSG001")
        self.assertEqual(msg.version, "2.5")

    def test_accepts_newline_separators(self):
        msg = Message.parse(RAW.replace("\r", "\n"))
        self.assertEqual(len(msg.segments), 4)

    def test_lookup_helpers(self):
        msg = Message.parse(RAW)
        self.assertEqual(msg.first("OBX").value(5), "4.2")
        self.assertIsNone(msg.first("ZZZ"))
        self.assertEqual(len(msg.all("PID")), 1)

    def test_encode_round_trip(self):
        self.assertEqual(Message.parse(RAW).encode(), RAW)

    def test_custom_delimiters(self):
        raw = "MSH#*+!$#LIS#MAIN#CLN#MAIN#20250303##ADT*A01#C1#P#2.5\rPID#1##X"
        msg = Message.parse(raw)
        self.assertEqual(msg.message_type, "ADT^A01")
        self.assertEqual(msg.first("PID").value(3), "X")

    def test_rejects_empty_and_headerless_text(self):
        for bad in ("", "   ", "PID|1|2"):
            with self.assertRaises(Hl7Error):
                Message.parse(bad)
