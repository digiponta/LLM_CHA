import copy,unittest
from epistemic_holdout_v023370 import classify_v70,build_holdout,validate_and_score
from epistemic_calibration_v023368 import classify_v68
class HoldoutTests(unittest.TestCase):
    def test_opinion_recovery(self):
        self.assertEqual(classify_v68("量子力学的に考えると、こうなる。"),["CONTEXT_ONLY"])
        self.assertIn("OPINION",classify_v70("量子力学的に考えると、こうなる。"))
    def test_technical_possibility_not_hypothesis(self):
        self.assertNotIn("HYPOTHESIS",classify_v70("可能性の分布を記述する。"))
    def test_ambiguous_teki_niwa_remains_unresolved(self):
        self.assertEqual(classify_v70("量子力学的には時間を扱う。"),["CONTEXT_ONLY"])
    def test_analogy_and_opinion(self):
        self.assertEqual(set(classify_v70("現象論的な見方では、舞台のようなものだ。")),{"ANALOGY","OPINION"})
    def test_holdout_separately_authored(self):
        data=build_holdout()
        self.assertEqual(len(data["rows"]),8)
        self.assertTrue(all(r["review_status"]=="UNREVIEWED" and r["gold_labels"] is None for r in data["rows"]))
    def test_unreviewed_no_metrics(self):
        self.assertIsNone(validate_and_score(build_holdout())["metrics"])
    def test_reviewed_scores(self):
        data=build_holdout()
        row=data["rows"][0];row["review_status"]="REVIEWED";row["gold_labels"]=["OPINION"]
        self.assertEqual(validate_and_score(data)["reviewed_count"],1)
        self.assertIn("v70_labels",validate_and_score(data)["metrics"])
    def test_changed_source_rejected(self):
        data=build_holdout();data["rows"][0]["context"]="altered"
        with self.assertRaises(ValueError):validate_and_score(data)
    def test_modified_predictions_rejected(self):
        data=build_holdout();data["rows"][0]["v70_labels"]=["OPINION"]
        with self.assertRaises(ValueError):validate_and_score(data)
    def test_unreviewed_gold_rejected(self):
        data=build_holdout();data["rows"][0]["gold_labels"]=["OPINION"]
        with self.assertRaises(ValueError):validate_and_score(data)
    def test_bad_gold_rejected(self):
        data=build_holdout();row=data["rows"][0];row["review_status"]="REVIEWED";row["gold_labels"]=["TRUE"]
        with self.assertRaises(ValueError):validate_and_score(data)
if __name__=="__main__":unittest.main()
