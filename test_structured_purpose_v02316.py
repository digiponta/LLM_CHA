import unittest
from structured_purpose_holdout_v02316 import fixture
from evaluate_structured_purpose_v02316 import evaluate,summary,FIELDS
from semantic_purpose_estimator_v02314 import SemanticPurposeEstimator
class StructuredEvalTests(unittest.TestCase):
    def test_fixture_ids(self):
        rows=fixture()
        self.assertEqual(len(rows),22)
        self.assertEqual(len({r["id"] for r in rows}),len(rows))
    def test_expected_structure(self):
        for r in fixture():
            self.assertTrue(set(FIELDS).issubset(r))
            self.assertIsInstance(r["purposes"],list)
    def test_both_estimators(self):
        model=SemanticPurposeEstimator()
        for name in ("vector","structured"):
            rows=evaluate(fixture(),name,model)
            self.assertEqual(len(rows),22)
            self.assertTrue(all("score" in r for r in rows))
    def test_summary_bounds(self):
        rows=evaluate(fixture(),"structured",SemanticPurposeEstimator())
        metrics=summary(rows)
        self.assertEqual(metrics["all"]["total"],22)
        self.assertLessEqual(metrics["all"]["pass"],22)
        self.assertEqual(metrics["overcommit"]["denominator"],6)
    def test_purpose_order_measure(self):
        from evaluate_structured_purpose_v02316 import summary
        r={"score":{f:True for f in FIELDS}|{"purpose_set":True,"all":True},
           "expected":{"purposes":["development","learning"]},
           "predicted":{"purposes":["learning","development"]}}
        self.assertEqual(summary([r])["all"]["pass"],1)
        # Explicit order correctness is scored by field equality elsewhere.
if __name__=="__main__":unittest.main()
