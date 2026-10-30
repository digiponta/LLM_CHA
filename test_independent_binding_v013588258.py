import json
import unittest
from pathlib import Path
from evaluate_independent_binding_v013588258 import evaluate

class BindingEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=json.loads(Path("data/independent_binding_eval_v013588258.json").read_text(encoding="utf-8"))["cases"]

    def test_fixture_count_and_unique_ids(self):
        self.assertEqual(len(self.cases),12)
        self.assertEqual(len({item["id"] for item in self.cases}),12)

    def test_metrics_have_correct_denominators(self):
        report=evaluate(self.cases)
        self.assertEqual(report["positive_cases"]+report["negative_cases"],12)
        self.assertAlmostEqual(report["coverage"],report["accepted"]/12)
        self.assertEqual(report["false_accept"],report["accepted"]-report["correct_accept"])
        self.assertAlmostEqual(report["false_accept_rate"],report["negative_false_accept"]/report["negative_cases"])

    def test_historical_date_is_not_event_date(self):
        rows={r["id"]:r for r in evaluate(self.cases)["results"]}
        self.assertFalse(rows["ind-bang-history-negative"]["accepted"])
        self.assertFalse(rows["ind-bang-pronoun-negative"]["accepted"])

    def test_cause_abstention_exposes_recall_gap(self):
        rows={r["id"]:r for r in evaluate(self.cases)["results"]}
        self.assertFalse(rows["ind-universe-cause-explanation-positive"]["accepted"])
        self.assertTrue(rows["ind-universe-cause-explanation-positive"]["expected_answerable"])

    def test_unknown_subject_does_not_cross_bind(self):
        rows={r["id"]:r for r in evaluate(self.cases)["results"]}
        self.assertFalse(rows["ind-other-subject-negative"]["accepted"])

if __name__=="__main__":
    unittest.main()
