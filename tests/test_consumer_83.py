import unittest

from clinkit import contract, consumer_83


class ExportTests(unittest.TestCase):
    def test_export_line(self):
        rec = contract.Record("CL-9", 700, "open")
        self.assertEqual(consumer_83.export_line(rec), "CL-9,700")
