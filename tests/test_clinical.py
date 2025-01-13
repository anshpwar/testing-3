import datetime as dt
import unittest
from decimal import Decimal

from clinkit import clinical, identifiers, rules


class IdentifierTests(unittest.TestCase):
    def test_mrn_round_trip(self):
        for seq in (0, 1, 18, 4242, 9999999):
            self.assertTrue(identifiers.valid_mrn(identifiers.make_mrn(seq)))

    def test_mrn_detects_single_digit_errors(self):
        mrn = identifiers.make_mrn(1234)
        for pos in range(3, 10):
            digit = (int(mrn[pos]) + 1) % 10
            self.assertFalse(identifiers.valid_mrn(mrn[:pos] + str(digit) + mrn[pos + 1:]))

    def test_mrn_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            identifiers.make_mrn(10 ** 7)

    def test_other_numbers(self):
        self.assertEqual(identifiers.order_number(7, 1), "LO1-000007")
        self.assertEqual(identifiers.invoice_number(2025, 12), "INV-2025-00012")

    def test_phone(self):
        self.assertEqual(identifiers.normalise_phone("(555) 010-0199"), "555-010-0199")
        self.assertEqual(identifiers.normalise_phone("1-555-010-0199"), "555-010-0199")
        with self.assertRaises(ValueError):
            identifiers.normalise_phone("12345")


class ClinicalTests(unittest.TestCase):
    def test_age_years(self):
        birth = dt.date(1980, 6, 15)
        self.assertEqual(clinical.age_years(birth, dt.date(2025, 6, 14)), 44)
        self.assertEqual(clinical.age_years(birth, dt.date(2025, 6, 15)), 45)

    def test_bmi(self):
        self.assertEqual(clinical.bmi(Decimal("70"), 170), Decimal("24.2"))
        with self.assertRaises(ValueError):
            clinical.bmi(None, 170)

    def test_dose_ceiling_follows_the_policy_table(self):
        for weight in (8, 25, 70, 120):
            self.assertEqual(clinical.dose_ceiling(weight), rules.dose_ceiling_mg(weight))
        self.assertEqual(clinical.dose_ceiling(Decimal("70.9")), rules.dose_ceiling_mg(70))

    def test_abnormal_flags(self):
        self.assertEqual(clinical.abnormal_flag("4.0", "3.5", "5.1"), "N")
        self.assertEqual(clinical.abnormal_flag("3.4", "3.5", "5.1"), "L")
        self.assertEqual(clinical.abnormal_flag("5.2", "3.5", "5.1"), "H")
        self.assertEqual(clinical.abnormal_flag("2.0", "3.5", "5.1"), "LL")
        self.assertEqual(clinical.abnormal_flag("7.0", "3.5", "5.1"), "HH")
        self.assertEqual(clinical.abnormal_flag("3.5", "3.5", "5.1"), "N")

    def test_fall_risk_and_bands(self):
        self.assertEqual(clinical.fall_risk(80, 2), rules.fall_risk_points(80) + 4)
        self.assertEqual(clinical.risk_band(0), "low")
        self.assertEqual(clinical.risk_band(4), "moderate")
        self.assertEqual(clinical.risk_band(9), "high")

    def test_daily_dose(self):
        self.assertEqual(clinical.daily_dose_mg(250, 3), 750)
