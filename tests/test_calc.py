import unittest

from clinkit import calc


class CalcTests(unittest.TestCase):
    def test_combined_charge(self):
        self.assertEqual(calc.combined_charge(0), 5700)
        self.assertEqual(calc.combined_charge(1), 5700)
        self.assertEqual(calc.combined_charge(15), 5700)
        self.assertEqual(calc.combined_charge(16), 10000)
