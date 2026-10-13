import unittest
from evaluate_japanese_proposition_v0411 import CASES,evaluate,synthetic_evidence
from article_proposition_alignment_v0410 import align

class GeneralizationEvaluationTests(unittest.TestCase):
    def test_case_count(self):self.assertEqual(len(CASES),20)
    def test_deterministic(self):self.assertEqual(evaluate(),evaluate())
    def test_confusion_total(self):
        d=evaluate()
        self.assertEqual(d["tp"]+d["fp"]+d["fn"]+d["tn"],d["total"])
    def test_known_pattern_recovered(self):
        rows={r["id"]:r for r in evaluate()["details"]}
        self.assertTrue(rows["simple-dearu"]["predicted_extract"])
    def test_expected_unseen_form_omitted(self):
        rows={r["id"]:r for r in evaluate()["details"]}
        self.assertFalse(rows["toha"]["predicted_extract"])
        self.assertTrue(rows["toha"]["expected_extract"])
    def test_negative_does_not_assert(self):
        rows={r["id"]:r for r in evaluate()["details"]}
        self.assertFalse(rows["negation"]["predicted_extract"])
    def test_no_promotion(self):
        d=evaluate()
        self.assertEqual(d["truth_promotions"],0)
        self.assertEqual(d["semantic_memory_writes"],0)
        self.assertFalse(d["training_enabled"])
    def test_exact_span(self):
        d=align(synthetic_evidence("小説は文学である。"))
        p=d["propositions"][0]
        self.assertEqual(p["evidence_text"],"小説は文学である。")
    def test_duplicate_cases_fail_closed(self):
        with self.assertRaises(ValueError):evaluate([CASES[0],CASES[0]])
    def test_metrics_range(self):
        d=evaluate()
        for key in ("precision","recall","balanced_accuracy"):
            self.assertTrue(d[key] is None or 0<=d[key]<=1)
if __name__=="__main__":unittest.main()
