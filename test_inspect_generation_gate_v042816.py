"""Synthetic tests for v0.4.28.16 review packet."""
import unittest
from inspect_generation_gate_v042816 import build_packet

class Tests(unittest.TestCase):
    def fixture(self):
        entries=[]
        for i in range(64):
            ident=("A04","A05","C05","C07")[i] if i<4 else f"T{i:02d}"
            entries.append({"id":ident,"turn":1,"question":"質問","final_answer":"回答",
              "gate_resolution":"ACCEPT","semantic_agreement":0.86,
              "candidate_alignment":"SINGLE_TURN_CONFIRMED",
              "primary_text":"候補","candidates":[{"seed":0,"text":"候補"}],
              "human_final_relevant":None})
        return {"entries":entries}
    def test_four_focused(self):
        r=build_packet(self.fixture())
        self.assertEqual([x["id"] for x in r["cases"]],["A04","A05","C05","C07"])
    def test_unlabeled_not_failure(self):
        r=build_packet(self.fixture())
        self.assertEqual(r["human_final_relevance_labeled"],0)
        self.assertTrue(all(x["gate_acceptance_status"]=="NOT_EVALUATED" for x in r["cases"]))
    def test_human_labeled_conflict(self):
        q=self.fixture();q["entries"][0]["human_final_relevant"]=False
        r=build_packet(q)
        self.assertEqual(r["cases"][0]["gate_acceptance_status"],"HUMAN_LABELED_IRRELEVANT_ACCEPT")
        self.assertEqual(r["cases"][0]["causal_attribution"],"UNDETERMINED")
    def test_missing_focus(self):
        q=self.fixture();q["entries"][0]["id"]="OTHER"
        with self.assertRaises(ValueError):build_packet(q)
    def test_ambiguous_candidates(self):
        q=self.fixture();q["entries"][0]["candidate_alignment"]="MULTITURN_UNRESOLVED"
        with self.assertRaises(ValueError):build_packet(q)
if __name__=="__main__":unittest.main()
