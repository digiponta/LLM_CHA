"""v0.4.28.20 review worksheet tests."""
import unittest
from export_qa_review_worksheet_v042820 import worksheet
from review_semantic_relevance_v042813 import FIELDS
class Tests(unittest.TestCase):
    def data(self):
        return {"records":[{"id":f"T{i:02d}","turn":1,"question":"Q","final_answer":"A","gate_resolution":"ACCEPT","candidate_alignment":"SINGLE_TURN_CONFIRMED","literal_probe_identity":False,"manual_review":{}} for i in range(60)]+[
           {"id":x,"turn":1,"question":"Q","final_answer":"A","gate_resolution":"ACCEPT","candidate_alignment":"SINGLE_TURN_CONFIRMED","literal_probe_identity":False,"manual_review":{}} for x in ("A04","A05","C05","C07")]}
    def test_count(self):
        self.assertEqual(len(worksheet(self.data())),64)
    def test_focus_first(self):
        self.assertEqual([x["id"] for x in worksheet(self.data())[:4]],["A04","A05","C05","C07"])
    def test_blank_labels(self):
        self.assertTrue(all(x["final_relevant"]=="" for x in worksheet(self.data())))
    def test_compatible_schema(self):
        self.assertEqual(list(worksheet(self.data())[0]),FIELDS)
    def test_duplicate_rejected(self):
        d=self.data();d["records"][0]["id"]=d["records"][1]["id"]
        with self.assertRaises(ValueError):worksheet(d)
if __name__=="__main__":unittest.main()
