"""Tests for v0.4.28.19 calibration inventory."""
import unittest
from prepare_qa_calibration_v042819 import inventory
from review_semantic_relevance_v042813 import template
class Tests(unittest.TestCase):
    def fixture(self):
        ids=["A04","A05","C05","C07"]+[f"T{i:02d}" for i in range(60)]
        v={"records":[{"id":x,"turn":1,"question":"量子力学とは","final_answer":"量子力学の説明",
            "gate_resolution":"ACCEPT","candidate_alignment":"SINGLE_TURN_CONFIRMED",
            "literal_probe_identity":False,"manual_review":{}} for x in ids]}
        rows=[{k:("" if val is None else str(val)) for k,val in row.items()} for row in template(v)]
        return v,rows
    def test_no_labels(self):
        v,rows=self.fixture();r=inventory(v,rows)
        self.assertEqual((r["positive_labeled"],r["negative_labeled"],r["unlabeled"]),(0,0,64))
    def test_focus_unlabeled_first(self):
        v,rows=self.fixture();r=inventory(v,rows)
        self.assertEqual([x["id"] for x in r["records"][:4]],["A04","A05","C05","C07"])
    def test_both_labels(self):
        v,rows=self.fixture();rows[0]["final_relevant"]="false";rows[4]["final_relevant"]="true"
        r=inventory(v,rows)
        self.assertTrue(r["balanced_binary_calibration_ready"])
        self.assertEqual((r["positive_labeled"],r["negative_labeled"]),(1,1))
    def test_no_auto_labels(self):
        v,rows=self.fixture();r=inventory(v,rows)
        self.assertEqual(r["automatic_labels_added"],0)
        self.assertFalse(r["threshold_estimated"])
    def test_invalid_label(self):
        v,rows=self.fixture();rows[0]["final_relevant"]="maybe"
        with self.assertRaises(ValueError):inventory(v,rows)
if __name__=="__main__":unittest.main()
