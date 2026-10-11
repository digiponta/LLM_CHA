import unittest
from structural_evidence_integration_v023360 import evaluate

class StructuralEvidenceIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=evaluate()
    def test_all_cases(self):
        self.assertEqual(self.report["total"],11)
        self.assertEqual(self.report["passed"],11,
            [x for x in self.report["cases"] if not x["passed"]])
    def test_positive_and_negative_paths(self):
        rows={r["case"]:r for r in self.report["cases"]}
        for case in ("matching_is_a","matching_includes","matching_conditional",
                     "negative_polarity","reverse_relation","missing_condition",
                     "unverified","raw_corpus","unsupported_language",
                     "cross_context","mapping_invalidation"):
            with self.subTest(case=case):
                self.assertTrue(rows[case]["passed"])
    def test_no_production_write(self):
        self.assertFalse(self.report["production_semantic_memory_changed"])
        self.assertFalse(self.report["model_training"])
if __name__=="__main__":
    unittest.main()
