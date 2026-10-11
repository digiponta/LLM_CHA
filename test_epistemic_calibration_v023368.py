import json,tempfile,unittest
from pathlib import Path
from epistemic_calibration_v023368 import classify_v68,dataset,evaluate_reviewed

class EpistemicCalibrationTests(unittest.TestCase):
    def test_possible_not_automatically_hypothesis(self):
        self.assertNotIn("HYPOTHESIS",classify_v68("可能性の集合として扱う。"))
    def test_explicit_hedge(self):
        self.assertIn("HYPOTHESIS",classify_v68("そうかもしれない。"))
    def test_analogy(self):
        self.assertIn("ANALOGY",classify_v68("零点エネルギーのアナロジ。"))
    def test_opinion(self):
        self.assertIn("OPINION",classify_v68("これは現象論的な見方。"))
    def test_overlap(self):
        s="私の観点では、宇宙は映像のようなもの。"
        self.assertEqual(set(classify_v68(s)),{"ANALOGY","OPINION"})
    def test_unreviewed_no_scores(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"sample.txt"
            p.write_text("量子力学では確率を扱う。",encoding="utf8")
            r=dataset(p,"量子力学")
            self.assertEqual(r["sample_count"],1)
            self.assertIsNone(r["metrics"])
            self.assertEqual(evaluate_reviewed(r["rows"])["metrics"],None)
    def test_reviewed_gold_metrics(self):
        rows=[{"review_status":"REVIEWED","gold_labels":["HYPOTHESIS"],
               "baseline_labels":["HYPOTHESIS"],"candidate_labels":["CONTEXT_ONLY"]}]
        scores=evaluate_reviewed(rows)
        self.assertEqual(scores["reviewed_count"],1)
        self.assertEqual(scores["metrics"]["baseline"]["micro_f1"],1)
        self.assertEqual(scores["metrics"]["candidate"]["micro_f1"],0)
    def test_invalid_gold_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_reviewed([{"review_status":"REVIEWED","gold_labels":["TRUE"],
                                "baseline_labels":[],"candidate_labels":[]}])
    def test_mixed_review_uses_reviewed_only(self):
        rows=[{"review_status":"REVIEWED","gold_labels":["OPINION"],
               "baseline_labels":["OPINION"],"candidate_labels":["OPINION"]},
              {"review_status":"UNREVIEWED","gold_labels":None,
               "baseline_labels":["HYPOTHESIS"],"candidate_labels":["CONTEXT_ONLY"]}]
        self.assertEqual(evaluate_reviewed(rows)["reviewed_count"],1)

if __name__=="__main__":unittest.main()
