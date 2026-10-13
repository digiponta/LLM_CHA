"""Regression tests for v0.4.28.15 review queue."""
import unittest
from prepare_gate_review_queue_v042815 import build_queue

class QueueTests(unittest.TestCase):
    def fixtures(self):
        a=[];b=[]
        for i in range(1,65):
            ident="A04" if i==4 else "T"+str(i)
            a.append({"id":ident,"turn":1,"question":"Q","final_answer":"A",
                      "gate_resolution":"ACCEPT","candidate_alignment":"SINGLE_TURN_CONFIRMED",
                      "primary_text":"A","observed_candidates":[{"seed":0,"text":"A"}]})
            b.append({"id":ident,"turn":1,"gate_resolution":"ACCEPT",
                      "semantic_agreement":0.8,"human_final_relevant":None})
        return {"records":a},{"records":b}
    def test_64(self):
        a,b=self.fixtures()
        r=build_queue(a,b)
        self.assertEqual(r["queue_length"],64)
        self.assertEqual(r["human_labeled"],0)
    def test_focus_priority(self):
        a,b=self.fixtures()
        self.assertEqual(build_queue(a,b)["entries"][0]["id"],"A04")
    def test_human_conflict_priority(self):
        a,b=self.fixtures()
        b["records"][1]["human_final_relevant"]=False
        r=build_queue(a,b)
        self.assertEqual(r["entries"][0]["id"],"T2")
        self.assertFalse(r["automatic_quality_judgments"])
    def test_mismatch(self):
        a,b=self.fixtures()
        b["records"][0]["gate_resolution"]="GATE_REVIEW"
        with self.assertRaises(ValueError):build_queue(a,b)
    def test_no_multiturn_guess(self):
        a,b=self.fixtures()
        a["records"][0]["candidate_alignment"]="MULTITURN_UNRESOLVED"
        with self.assertRaises(ValueError):build_queue(a,b)

if __name__=="__main__":unittest.main()
