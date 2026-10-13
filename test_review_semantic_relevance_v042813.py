"""v0.4.28.13 manual-label import and source integrity tests."""
import unittest
from review_semantic_relevance_v042813 import template,summarize,FIELDS
class Tests(unittest.TestCase):
    def fixture(self):
        return {"records":[{"id":f"T{i:02d}","turn":1,"question":"質問",
                 "final_answer":"応答","gate_resolution":"ACCEPT",
                 "candidate_alignment":"SINGLE_TURN_CONFIRMED",
                 "literal_probe_identity":False,"manual_review":{}} for i in range(1,65)]}
    def review_rows(self):
        d=self.fixture()
        return d, [{k:("" if v is None else str(v)) for k,v in row.items()} for row in template(d)]
    def test_template(self):
        self.assertEqual(len(template(self.fixture())),64)
        self.assertEqual(template(self.fixture())[0]["final_relevant"],"")
    def test_blank_unscored(self):
        d,rows=self.review_rows()
        self.assertEqual(summarize(d,rows)["reviewed_turns"],0)
    def test_explicit_conflict(self):
        d,rows=self.review_rows()
        rows[0]["final_relevant"]="false"
        r=summarize(d,rows)
        self.assertEqual(r["reviewed_turns"],1)
        self.assertEqual(r["labeled_accept_relevance_conflicts"],1)
    def test_tampering_rejected(self):
        d,rows=self.review_rows()
        rows[0]["gate_resolution"]="GATE_REVIEW"
        with self.assertRaises(ValueError):summarize(d,rows)
    def test_invalid_label_rejected(self):
        d,rows=self.review_rows()
        rows[0]["final_relevant"]="maybe"
        with self.assertRaises(ValueError):summarize(d,rows)
if __name__=="__main__":unittest.main()
