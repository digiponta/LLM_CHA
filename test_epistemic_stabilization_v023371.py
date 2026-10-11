import copy,unittest
from epistemic_stabilization_v023371 import classify_v71,worksheet,evaluate

class StabilizationTests(unittest.TestCase):
    def test_h01_restoration(self):
        self.assertIn("OPINION",classify_v71("私の解釈では、この現象は別の説明も可能だ。"))
    def test_explicit_personal_view(self):
        self.assertIn("OPINION",classify_v71("私の見解では違う。"))
    def test_possibility_not_hedge(self):
        self.assertNotIn("HYPOTHESIS",classify_v71("可能性の分布を計算する。"))
    def test_ambiguous_teki_niwa(self):
        self.assertEqual(classify_v71("量子力学的には結果を扱う。"),["CONTEXT_ONLY"])
    def test_multi_label(self):
        self.assertEqual(set(classify_v71("私の解釈では舞台のようなものだ。")),{"ANALOGY","OPINION"})
    def test_unreviewed_probes(self):
        data=worksheet()
        self.assertEqual(len(data["rows"]),12)
        self.assertTrue(all(r["gold_labels"] is None and r["review_status"]=="UNREVIEWED" for r in data["rows"]))
    def test_no_scores_without_gold(self):
        self.assertIsNone(evaluate(worksheet())["metrics"])
    def test_reviewed_one(self):
        data=worksheet();data["rows"][0].update(review_status="REVIEWED",gold_labels=["OPINION"])
        self.assertEqual(evaluate(data)["reviewed_count"],1)
        self.assertIn("v71_labels",evaluate(data)["metrics"])
    def test_changed_predictions_rejected(self):
        data=worksheet();data["rows"][0]["v71_labels"]=["CONTEXT_ONLY"]
        with self.assertRaises(ValueError):evaluate(data)
    def test_changed_text_rejected(self):
        data=worksheet();data["rows"][0]["context"]="different"
        with self.assertRaises(ValueError):evaluate(data)
    def test_invalid_gold_rejected(self):
        data=worksheet();data["rows"][0].update(review_status="REVIEWED",gold_labels=["TRUE"])
        with self.assertRaises(ValueError):evaluate(data)
    def test_duplicate_gold_rejected(self):
        data=worksheet();data["rows"][0].update(review_status="REVIEWED",gold_labels=["OPINION","OPINION"])
        with self.assertRaises(ValueError):evaluate(data)

if __name__=="__main__":unittest.main()
