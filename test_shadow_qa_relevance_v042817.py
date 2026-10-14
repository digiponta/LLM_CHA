"""v0.4.28.17 offline shadow non-operational tests."""
import unittest
from review_semantic_relevance_v042813 import template
from shadow_qa_relevance_v042817 import shadow
class Tests(unittest.TestCase):
    def fixture(self):
        v={"records":[{"id":f"X{i:02d}","turn":1,"question":"Q","final_answer":"A",
            "gate_resolution":"ACCEPT","candidate_alignment":"SINGLE_TURN_CONFIRMED",
            "literal_probe_identity":False,"manual_review":{}} for i in range(64)]}
        c={"records":[{"id":f"X{i:02d}","turn":1,"gate_resolution":"ACCEPT",
            "semantic_agreement":0.86,"human_final_relevant":None} for i in range(64)]}
        reviews=[{k:("" if value is None else str(value)) for k,value in row.items()} for row in template(v)]
        return v,c,reviews
    def test_empty_labels_unassessed(self):
        v,c,rows=self.fixture();r=shadow(v,c,rows)
        self.assertEqual((r["reviewed"],r["accepted_irrelevant"]),(0,0))
    def test_explicit_irrelevant_accept(self):
        v,c,rows=self.fixture();rows[0]["final_relevant"]="false"
        r=shadow(v,c,rows)
        self.assertEqual((r["reviewed"],r["accepted_irrelevant"]),(1,1))
        self.assertTrue(r["shadow_not_operational"])
    def test_explicit_relevant_accept(self):
        v,c,rows=self.fixture();rows[0]["final_relevant"]="true"
        self.assertEqual(shadow(v,c,rows)["accepted_relevant"],1)
    def test_stale_conflict_rejected(self):
        v,c,rows=self.fixture();c["records"][0]["human_final_relevant"]=False
        rows[0]["final_relevant"]="true"
        with self.assertRaises(ValueError):shadow(v,c,rows)
    def test_no_runtime_modifications(self):
        v,c,rows=self.fixture()
        self.assertTrue(all(not x["runtime_gate_modified"] for x in shadow(v,c,rows)["records"]))
if __name__=="__main__":unittest.main()
