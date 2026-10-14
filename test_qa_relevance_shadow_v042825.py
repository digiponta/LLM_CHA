import copy,unittest
from qa_relevance_shadow_v042825 import triage
class Tests(unittest.TestCase):
    def fixture(self):
        return {"records":[{"id":f"T{i:02d}","turn":1,
            "lexical_overlap":0.0 if i%2==0 else 0.2,
            "chatgpt_relevant":False if i%3==0 else True,
            "gate_resolution":"ACCEPT","semantic_agreement":0.95} for i in range(64)]}
    def test_review_only(self):
        r=triage(self.fixture());self.assertEqual(r["flagged_for_review"],32)
        self.assertFalse(r["truth_gate_modified"])
    def test_label_independent(self):
        a=self.fixture();b=copy.deepcopy(a)
        for row in b["records"]:row["chatgpt_relevant"]=not row["chatgpt_relevant"]
        left=triage(a);right=triage(b)
        self.assertEqual([x["shadow_decision"] for x in left["records"]],
                         [x["shadow_decision"] for x in right["records"]])
    def test_gate_independent(self):
        a=self.fixture();b=copy.deepcopy(a)
        for row in b["records"]:row["gate_resolution"]="GATE_REVIEW"
        self.assertEqual([x["shadow_decision"] for x in triage(a)["records"]],
                         [x["shadow_decision"] for x in triage(b)["records"]])
    def test_missing_overlap_abstains(self):
        a=self.fixture();a["records"][0]["lexical_overlap"]=None
        self.assertEqual(triage(a)["records"][0]["shadow_decision"],"NO_SIGNAL")
    def test_duplicate_rejected(self):
        a=self.fixture();a["records"][0]["id"]=a["records"][1]["id"]
        with self.assertRaises(ValueError):triage(a)
    def test_no_threshold_training(self):
        r=triage(self.fixture())
        self.assertFalse(r["threshold_fitted"])
        self.assertFalse(r["human_ground_truth"])
if __name__=="__main__":unittest.main()
