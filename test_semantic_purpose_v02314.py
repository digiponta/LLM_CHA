import unittest
from semantic_purpose_estimator_v02314 import SemanticPurposeEstimator,grams
from evaluate_semantic_purpose_v02314 import fresh_cases,evaluate
class SemanticPurposeTests(unittest.TestCase):
    def test_grams(self):
        self.assertIn("py",grams("Python"))
    def test_classes(self):
        model=SemanticPurposeEstimator()
        self.assertEqual(len(model.examples),4)
    def test_known_anchor(self):
        model=SemanticPurposeEstimator()
        r=model.predict("LLMを自作する")
        self.assertEqual(r["purpose"],"development")
        self.assertTrue(r["accepted"])
    def test_abstain_unrelated(self):
        self.assertIsNone(SemanticPurposeEstimator().predict("1234567890")["purpose"])
    def test_margin_threshold(self):
        model=SemanticPurposeEstimator()
        self.assertIsNone(model.predict("LLMを自作する",threshold=1.1)["purpose"])
    def test_fresh_fixture(self):
        cases=fresh_cases()
        self.assertEqual(len(cases),15)
        self.assertEqual(len({r["id"] for r in cases}),15)
    def test_result_structure(self):
        rows=evaluate(fresh_cases(),"semantic",SemanticPurposeEstimator(),0.25,0.04)
        self.assertEqual(len(rows),15)
        self.assertTrue(all("details" in r and "correct" in r for r in rows))
if __name__=="__main__":unittest.main()
