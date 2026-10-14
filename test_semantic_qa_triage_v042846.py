import unittest
from semantic_qa_triage_v042846 import analyze, inspect
from review_precision_v042845 import sample

def fixture():
    audit = {"version":"v0.4.28.44","mode":"CONTEXT_QA_HEURISTIC_AUDIT",
             "accepted":0,"train_ready":False,"audited_context":2,
             "audit_records":[{"id":f"id{i}", "source_line":i+1,"question":"元気ですか？",
              "answer":"元気です。","review_status":"pending","train_eligible":False} for i in range(2)]}
    return sample(audit, 2)

class SemanticQATriageTests(unittest.TestCase):
    def test_empty(self):
        self.assertIn("empty_text", inspect("", "abc"))
    def test_shift(self):
        self.assertIn("possible_topic_shift", inspect("元気ですか？","ところで別の話です。"))
    def test_pronoun(self):
        self.assertIn("context_dependent_expression", inspect("理由は？","それが原因です。"))
    def test_uncertainty(self):
        self.assertIn("uncertain_answer", inspect("正解は？","不明です。"))
    def test_answer_question(self):
        self.assertIn("answer_looks_like_question", inspect("元気ですか？","元気ですか？"))
    def test_negative(self):
        self.assertIn("negative_answer_review", inspect("できますか？","できません。"))
    def test_pending(self):
        result=analyze(fixture())
        self.assertEqual(result["accepted"],0)
        self.assertFalse(result["train_ready"])
        self.assertFalse(result["runtime_modified"])
    def test_preserves_ids(self):
        s=fixture()
        self.assertEqual({r["id"] for r in analyze(s)["records"]},{r["id"] for r in s["records"]})
    def test_duplicate_id_rejected(self):
        s=fixture()
        s["records"][1]["id"]=s["records"][0]["id"]
        with self.assertRaises(ValueError): analyze(s)
    def test_approved_rejected(self):
        s=fixture()
        s["records"][0]["review_status"]="approved"
        with self.assertRaises(ValueError): analyze(s)
    def test_invalid_rating_rejected(self):
        s=fixture()
        s["records"][0]["ratings"]["relevance"]="excellent"
        with self.assertRaises(ValueError): analyze(s)

if __name__=="__main__":
    unittest.main()
