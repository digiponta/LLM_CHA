import unittest
from plan_qa_manual_review_v042821 import plan
from review_semantic_relevance_v042813 import template

class Tests(unittest.TestCase):
    def fixture(self):
        ids=["A04","A05","C05","C07"]+[f"T{i:02d}" for i in range(60)]
        v={"records":[{"id":id,"turn":1,"question":"こんにちは","final_answer":"こんにちは","gate_resolution":"ACCEPT",
           "candidate_alignment":"SINGLE_TURN_CONFIRMED","literal_probe_identity":False,"manual_review":{}} for id in ids]}
        rows=[{k:("" if val is None else str(val)) for k,val in r.items()} for r in template(v)]
        return v,rows
    def test_blank(self):
        v,rows=self.fixture();r=plan(v,rows)
        self.assertEqual((r["unlabeled"],len(r["batches"])),(64,8))
    def test_focus_first(self):
        v,rows=self.fixture();r=plan(v,rows)
        self.assertEqual([x["id"] for x in r["batches"][0]["items"][:4]],["A04","A05","C05","C07"])
    def test_explicit_labels(self):
        v,rows=self.fixture();rows[0]["final_relevant"]="false";rows[4]["final_relevant"]="true"
        r=plan(v,rows)
        self.assertEqual((r["negative"],r["positive"],r["unlabeled"]),(1,1,62))
    def test_reject_incomplete_worksheet(self):
        v,rows=self.fixture()
        with self.assertRaises(ValueError):plan(v,rows[:-1])
    def test_no_gate_change(self):
        v,rows=self.fixture();r=plan(v,rows,5)
        self.assertFalse(r["truth_gate_modified"])
        self.assertEqual(r["automatic_labels_added"],0)
        self.assertEqual(len(r["batches"]),13)
if __name__=="__main__":unittest.main()
