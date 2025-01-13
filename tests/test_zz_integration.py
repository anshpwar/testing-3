import unittest

from clinkit import contract, pipeline


class PipelineIntegrationTests(unittest.TestCase):
    def test_pipeline_renders_fixed_width_lines(self):
        records = [contract.Record("CL-1", 1250, "open"), contract.Record("CL-2", 40, "closed")]
        result = pipeline.run_pipeline(records)
        self.assertEqual(result["retries"], 3)
        self.assertEqual(len(result["lines"]), 2)
        self.assertTrue(all(len(line) == 40 for line in result["lines"]))
        self.assertIn("1250 USD", result["lines"][0])
