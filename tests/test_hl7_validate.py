import datetime as dt
import unittest

from clinkit.hl7 import Message
from clinkit.hl7_validate import is_number, parse_timestamp, validate

GOOD = (
    "MSH|^~\\&|LIS|MAIN|CLINKIT|MAIN|20250303090000||ORU^R01|MSG001|P|2.5\r"
    "PID|1||MRN00000018||Testson^Pat||19800615|F\r"
    "OBR|1|LO3-000001||K^Potassium\r"
    "OBX|1|NM|K^Potassium||4.2|mmol/L|3.5-5.1|N\r"
)


def codes(text):
    return sorted(i.code for i in validate(Message.parse(text)))


class TimestampTests(unittest.TestCase):
    def test_precisions(self):
        self.assertEqual(parse_timestamp("2025"), dt.datetime(2025, 1, 1))
        self.assertEqual(parse_timestamp("202503"), dt.datetime(2025, 3, 1))
        self.assertEqual(parse_timestamp("20250303"), dt.datetime(2025, 3, 3))
        self.assertEqual(parse_timestamp("2025030309"), dt.datetime(2025, 3, 3, 9))
        self.assertEqual(parse_timestamp("20250303091530"), dt.datetime(2025, 3, 3, 9, 15, 30))

    def test_invalid(self):
        for bad in ("", "2025x303", "202503031", "20251301"):
            with self.assertRaises(ValueError):
                parse_timestamp(bad)

    def test_is_number(self):
        self.assertTrue(is_number("4.2"))
        self.assertFalse(is_number("high"))


class ValidateTests(unittest.TestCase):
    def test_good_message_has_no_issues(self):
        self.assertEqual(codes(GOOD), [])

    def test_missing_control_id(self):
        self.assertEqual(codes(GOOD.replace("MSG001", "")), ["missing-control-id"])

    def test_unsupported_version(self):
        self.assertEqual(codes(GOOD.replace("|2.5", "|1.0")), ["unsupported-version"])

    def test_missing_required_segment(self):
        self.assertEqual(codes(GOOD.replace("OBR|1|LO3-000001||K^Potassium\r", "")), ["missing-segment"])

    def test_unknown_message_type(self):
        self.assertEqual(codes(GOOD.replace("ORU^R01", "XYZ^Q9")), ["unknown-type"])

    def test_patient_checks(self):
        self.assertEqual(codes(GOOD.replace("MRN00000018", "")), ["missing-patient-id"])
        self.assertEqual(codes(GOOD.replace("19800615", "1980xx")), ["bad-birth-date"])
        self.assertEqual(codes(GOOD.replace("|F\r", "|Q\r")), ["bad-sex"])

    def test_observation_checks(self):
        self.assertEqual(codes(GOOD.replace("|NM|", "|QQ|")), ["bad-value-type"])
        self.assertEqual(codes(GOOD.replace("||4.2|", "||high|")), ["non-numeric-result"])

    def test_bad_header_timestamp(self):
        self.assertEqual(codes(GOOD.replace("20250303090000", "soon")), ["bad-timestamp"])

    def test_multiple_issues_are_all_reported(self):
        text = GOOD.replace("MSG001", "").replace("|2.5", "|1.0")
        self.assertEqual(codes(text), ["missing-control-id", "unsupported-version"])
