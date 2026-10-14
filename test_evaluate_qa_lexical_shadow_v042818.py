import unittest
from evaluate_qa_lexical_shadow_v042818 import bigrams,evaluate
from review_semantic_relevance_v042813 import template

class Tests(unittest.TestCase):
    def fixture(self):
        v={"records":[{"id":f"T{i:02d}","turn":1,"question":"量子力学とは",
            "final_answer":"量子力学は物理学です","gate_resolution":"ACCEPT",
            "candidate_alignment":"SINGLE_TURN_CONFIRMED",
            "literal_probe_identity":False,"manual_review":{}} for i in range(64)]}
        reviews=[{k:("" if value is None else str(value)) for k,value in row.items()} for row in template(v)]
        return v,reviews
    def test_overlap(self):
        self.assertIn("量子",bigrams("量子力学"))
    def test_unlabeled(self):
        v,r=self.fixture();self.assertEqual(evaluate(v,r)["paired_labels"],0)
    def test_positive(self):
        v,r=self.fixture();r[0]["final_relevant"]="true"
        self.assertEqual(evaluate(v,r)["paired_positive"],1)
    def test_negative(self):
        v,r=self.fixture();r[0]["final_relevant"]="false"
        self.assertEqual(evaluate(v,r)["paired_negative"],1)
    def test_no_semantic_claim(self):
        v,r=self.fixture();result=evaluate(v,r)
        self.assertTrue(result["not_semantic_classifier"])
        self.assertTrue(all(not row["gate_modified"] for row in result["records"]))
if __name__=="__main__":unittest.main()
