import datetime as dt
import unittest

from clinkit.hl7 import Message
from clinkit.hl7_build import build_ack, build_adt, build_oru, format_timestamp
from clinkit.hl7_validate import validate

WHEN = dt.datetime(2025, 3, 3, 9, 30, 0)
PATIENT = {"mrn": "MRN00000018", "family_name": "Test|son", "given_name": "Pat", "birth": "19800615", "sex": "F"}


class BuildTests(unittest.TestCase):
    def test_format_timestamp(self):
        self.assertEqual(format_timestamp(WHEN), "20250303093000")

    def test_oru_is_valid_and_parses_back(self):
        msg = build_oru(PATIENT, [("4.2", "mmol/L", "3.5", "5.1", "N")], "C100", WHEN, "LO3-000001", "K", "Potassium")
        parsed = Message.parse(msg.encode())
        self.assertEqual(validate(parsed), [])
        self.assertEqual(parsed.message_type, "ORU^R01")
        self.assertEqual(parsed.first("OBR").value(2), "LO3-000001")
        self.assertEqual(parsed.first("OBX").value(5), "4.2")

    def test_delimiters_in_names_are_escaped(self):
        msg = build_oru(PATIENT, [("4.2", "mmol/L", "3.5", "5.1", "N")], "C100", WHEN, "LO3-000001", "K", "Potassium")
        encoded = msg.encode()
        self.assertIn("Test\\F\\son", encoded)
        self.assertEqual(Message.parse(encoded).first("PID").value(5, 1), "Test|son")

    def test_adt(self):
        msg = build_adt("A01", PATIENT, "C101", WHEN, location=["W1", "A1"])
        parsed = Message.parse(msg.encode())
        self.assertEqual(parsed.message_type, "ADT^A01")
        self.assertEqual(validate(parsed), [])
        self.assertEqual(parsed.first("PV1").value(3, 2), "A1")

    def test_ack_mirrors_the_original(self):
        original = build_oru(PATIENT, [("4.2", "mmol/L", "3.5", "5.1", "N")], "C100", WHEN, "LO3-000001", "K", "Potassium")
        ack = build_ack(Message.parse(original.encode()), "AA", "stored", WHEN)
        parsed = Message.parse(ack.encode())
        self.assertEqual(parsed.first("MSA").value(1), "AA")
        self.assertEqual(parsed.first("MSA").value(2), "C100")
        self.assertEqual(parsed.msh.value(3), "LIS")
        self.assertEqual(parsed.msh.value(5), "CLINKIT")
