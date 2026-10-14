import unittest
from inspect_qa_ranking_failures_v042832 import inspect
class Tests(unittest.TestCase):
    def fixture(self):
        records=[]
        for i,(split,label,score) in enumerate([
            ("TRAIN",True,.9),("TRAIN",False,.1),
            ("INTERNAL_GROUP_HOLDOUT",True,.3),
            ("INTERNAL_GROUP_HOLDOUT",True,.8),
            ("INTERNAL_GROUP_HOLDOUT",False,.6),
            ("INTERNAL_GROUP_HOLDOUT",False,.8)]):
            records.append({"id":f"X{i}","turn":1,"split":split,"weak_label":label,
              "uncalibrated_score":score,"decision":"ABSTAIN"})
        return {"version":"v0.4.28.30","mode":"INTERNAL_GROUPED_DEVELOPMENT_EVALUATION",
          "train_labeled":2,"holdout_labeled":4,"checkpoint_verified":True,"records":records}
    def test_pair_accounting(self):
        d=inspect(self.fixture())
        self.assertEqual((d["correct_pairs"],d["tied_pairs"],d["inverted_pairs"]),(1,1,2))
        self.assertEqual(d["positive_negative_pairs"],4)
        self.assertEqual(d["ranking_auc"],.375)
    def test_worst_inverse_first(self):
        d=inspect(self.fixture())
        self.assertEqual(d["worst_inverted_pairs"][0]["margin"],-.5)
    def test_no_holdout_claim(self):
        d=inspect(self.fixture())
        self.assertFalse(d["independent_external_holdout"])
        self.assertFalse(d["trained_or_calibrated"])
    def test_invalid_score_rejected(self):
        x=self.fixture();x["records"][-1]["uncalibrated_score"]=float("nan")
        with self.assertRaises(ValueError):inspect(x)
    def test_one_class_no_auc(self):
        x=self.fixture()
        for r in x["records"][2:]:r["weak_label"]=False
        d=inspect(x)
        self.assertIsNone(d["ranking_auc"])
        self.assertEqual(d["positive_negative_pairs"],0)
if __name__=="__main__":unittest.main()
