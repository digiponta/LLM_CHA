import unittest
from diagnose_qa_generalization_v042831 import summarize
class Tests(unittest.TestCase):
    def fixture(self):
        records=[{"id":f"T{i:02d}","turn":1,"split":"TRAIN" if i<4 else "INTERNAL_GROUP_HOLDOUT",
          "weak_label":i%2==1,"uncalibrated_score":0.8 if i%2 else 0.2,"decision":"ABSTAIN"} for i in range(8)]
        return {"version":"v0.4.28.30","mode":"INTERNAL_GROUPED_DEVELOPMENT_EVALUATION",
          "records":records,"train_labeled":4,"holdout_labeled":4,"checkpoint_verified":True}
    def test_auc(self):
        r=summarize(self.fixture());self.assertEqual(r["holdout_weak_label_ranking_auc"],1.0)
        self.assertEqual(r["holdout_positive_negative_pairs"],4)
    def test_without_positive(self):
        r=self.fixture()
        for x in r["records"][4:]:x["weak_label"]=False
        self.assertIsNone(summarize(r)["holdout_weak_label_ranking_auc"])
    def test_duplicate(self):
        r=self.fixture();r["records"][0]["id"]="T01"
        with self.assertRaises(ValueError):summarize(r)
    def test_out_of_range(self):
        r=self.fixture();r["records"][0]["uncalibrated_score"]=2.0
        with self.assertRaises(ValueError):summarize(r)
    def test_no_claimed_accuracy(self):
        r=summarize(self.fixture())
        self.assertFalse(r["external_holdout"])
        self.assertTrue(r["no_threshold_optimization"])
if __name__=="__main__":unittest.main()
