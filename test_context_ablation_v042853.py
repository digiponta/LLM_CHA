import unittest
from context_ablation_v042853 import variants, report, FIELDS

def review():
    rows=[]
    for n in range(2):
        rows.append({"id":f"rpc-train-{n}","question":"人: こんにちは\n相手: はい\n人: 元気ですか？",
            "answer":"元気です。","review_status":"ai_reviewed","train_eligible":False,
            "source_split":"train","source_line":n+1,
            "ratings":{k:"pass" for k in FIELDS}})
    return {"version":"v0.4.28.52","mode":"AI_ASSISTED_QA_REVIEW","sample_size":2,
            "train_ready":False,"human_verified":False,"records":rows}

class ContextAblationTests(unittest.TestCase):
    def test_extract_final_turn(self):
        self.assertEqual(variants("人: こんにちは\n相手: はい\n人: 元気ですか？")["last_user"],"元気ですか？")
    def test_invalid_missing_role(self):
        self.assertFalse(variants("人: A\nB")["format_valid"])
    def test_invalid_role_order(self):
        self.assertFalse(variants("人: A\n人: B")["format_valid"])
    def test_single_user_turn(self):
        self.assertTrue(variants("人: こんにちは")["format_valid"])
    def test_report(self):
        r=report(review())
        self.assertEqual(r["context_format_valid"],2)
        self.assertIsNone(r["ablations"]["full_context"]["accuracy"])
    def test_pending_training(self):
        r=report(review())
        self.assertFalse(r["train_ready"])
        self.assertFalse(r["runtime_modified"])
    def test_fail_quarantine(self):
        d=review()
        d["records"][1]["ratings"]["training_suitability"]="fail"
        self.assertEqual(report(d)["training_suitability_fail_ids"],["rpc-train-1"])
    def test_duplicate_rejection(self):
        d=review();d["records"][1]["id"]=d["records"][0]["id"]
        with self.assertRaises(ValueError):report(d)
    def test_unapproved_rejection(self):
        d=review();d["records"][0]["review_status"]="approved"
        with self.assertRaises(ValueError):report(d)
    def test_source_not_evaluation(self):
        self.assertFalse(report(review())["evaluation_ready"])

if __name__=="__main__":
    unittest.main()
