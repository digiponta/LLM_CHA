"""Synthetic tests for v0.4.28.12 independent validation axes."""
import unittest
from validate_semantic_probes_v042812 import analyze
class Tests(unittest.TestCase):
    def sample(self):
        rows=[{"id":f"A{i:02d}","turn":1,"question":"Q","final_answer":"A",
               "gate_resolution":"ACCEPT","candidate_alignment":"SINGLE_TURN_CONFIRMED",
               "observed_candidates":[{"text":"一致"},{"text":"一 致"}]} for i in range(1,53)]
        rows.extend({"id":f"F{j}","turn":t,"question":"Q","final_answer":"A",
                 "gate_resolution":"ACCEPT","candidate_alignment":"MULTITURN_UNRESOLVED",
                 "observed_candidates":[]} for j in range(1,5) for t in range(1,4))
        return {"records":rows}
    def test_shape(self):
        r=analyze(self.sample());self.assertEqual(r["total_turns"],64)
        self.assertEqual(r["literal_identity_evaluable"],52)
    def test_literal_only(self):
        r=analyze(self.sample())
        self.assertEqual(r["literal_identity_true"],52)
        self.assertEqual(r["manual_relevance_labeled"],0)
        self.assertEqual(r["records"][0]["semantic_probe_agreement"],"NOT_EVALUATED")
    def test_different_text(self):
        d=self.sample();d["records"][0]["observed_candidates"][1]["text"]="別文"
        self.assertEqual(analyze(d)["literal_identity_false"],1)
    def test_multiturn_not_assigned(self):
        d=self.sample();d["records"][-1]["observed_candidates"]=[{"text":"bad"}]
        with self.assertRaises(ValueError):analyze(d)
    def test_duplicate_rejected(self):
        d=self.sample();d["records"][1]["id"]=d["records"][0]["id"]
        with self.assertRaises(ValueError):analyze(d)
if __name__=="__main__":unittest.main()
