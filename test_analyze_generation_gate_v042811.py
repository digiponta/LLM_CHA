import unittest
from analyze_generation_gate_v042811 import analyze
class Tests(unittest.TestCase):
    def fixture(self):
        groups=[]
        for cat,n in (("A",12),("B",12),("C",8),("D",8),("E",8),("G",4)):
            for i in range(1,n+1):
                groups.append({"id":f"{cat}{i:02d}","turns":[{"question":"質問","response":"回答","gate":"[gate=KNOWN, resolution=ACCEPT]"}],
                  "stage_trace":{"generation_candidates":[{"event":"GENERATION_CANDIDATE","seed":0,"text":"回答"}]}})
        for i in range(1,5):
            groups.append({"id":f"F{i}","turns":[{"question":"質問","response":"回答","gate":None} for _ in range(3)],
                "stage_trace":{"generation_candidates":[{"event":"GENERATION_CANDIDATE","seed":0,"text":"回答"}]}})
        return {"groups":groups}
    def test_64_turns(self):
        r=analyze(self.fixture())
        self.assertEqual(r["total_turns"],64)
        self.assertEqual(r["single_turns_aligned"],52)
        self.assertEqual(r["multiturns_unresolved"],12)
    def test_primary_alignment(self):
        r=analyze(self.fixture())
        self.assertTrue(r["records"][0]["primary_matches_final"])
    def test_multi_not_misattributed(self):
        r=analyze(self.fixture())
        multi=next(x for x in r["records"] if x["id"]=="F1")
        self.assertIsNone(multi["candidate_count"])
        self.assertIsNone(multi["primary_text"])
    def test_requires_trace(self):
        d=self.fixture();d["groups"][0]["stage_trace"]=None
        with self.assertRaises(ValueError):analyze(d)
    def test_noncausal(self):
        r=analyze(self.fixture())
        self.assertFalse(r["causal_attribution_established"])
        self.assertEqual(r["records"][0]["causal_attribution"],"UNDETERMINED")
if __name__=="__main__":unittest.main()
