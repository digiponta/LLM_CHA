import unittest
from propose_qa_labels_llm_judge_v042823 import prepare,validate_judgment
from review_semantic_relevance_v042813 import template
class Tests(unittest.TestCase):
    def fixture(self):
        v={"records":[{"id":x,"turn":1,"question":"本を読むのは好き？","final_answer":"好きです。",
            "gate_resolution":"ACCEPT","candidate_alignment":"SINGLE_TURN_CONFIRMED",
            "literal_probe_identity":False,"manual_review":{}} for x in
            (["A04","A05","C05","C07"]+[f"T{i:02d}" for i in range(60)])]}
        reviews=[{k:("" if a is None else str(a)) for k,a in r.items()} for r in template(v)]
        return v,reviews
    def test_no_api_default(self):
        v,r=self.fixture();out=prepare(v,r)
        self.assertFalse(out["external_model_used"])
        self.assertEqual((out["proposed"],out["selected"]),(0,8))
    def test_prioritize_focus(self):
        v,r=self.fixture();out=prepare(v,r,4)
        self.assertEqual([x["id"] for x in out["records"]],["A04","A05","C05","C07"])
    def test_mock_judge_proposals_only(self):
        v,r=self.fixture()
        def fake(q,a):return {"verdict":"relevant","rationale":"質問に回答している","confidence":0.75}
        out=prepare(v,r,2,fake,"mock")
        self.assertEqual(out["proposed"],2)
        self.assertTrue(out["human_labels_modified"] is False)
        self.assertEqual(r[0]["final_relevant"],"")
        self.assertTrue(all(x["human_review_required"] for x in out["records"]))
    def test_skip_human_labeled(self):
        v,r=self.fixture();r[0]["final_relevant"]="false"
        out=prepare(v,r,64)
        self.assertEqual(out["total_available_unlabeled"],63)
        self.assertNotIn("A04",[x["id"] for x in out["records"]])
    def test_bad_judge_result_abstains(self):
        v,r=self.fixture()
        out=prepare(v,r,1,lambda q,a:{"verdict":"yes"},"mock")
        self.assertEqual(out["abstained"],1)
        self.assertEqual(out["proposed"],0)
    def test_schema_rejects_bool_confidence(self):
        with self.assertRaises(ValueError):
            validate_judgment({"verdict":"irrelevant","rationale":"無関係","confidence":True})
if __name__=="__main__":unittest.main()
