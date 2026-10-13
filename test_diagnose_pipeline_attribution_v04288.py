"""Synthetic tests for v0.4.28.8 diagnostic provenance."""
import unittest
from diagnose_pipeline_attribution_v04288 import diagnose
class Tests(unittest.TestCase):
    def sample(self):
        records=[{"id":f"A{i:02d}","turn":1,"question":str(i),"answer":"答え","gate_resolution":"ACCEPT"} for i in range(1,65)]
        return {"records":records}
    def test_undetermined(self):
        r=diagnose(self.sample())
        self.assertEqual(r["unattributed_turns"],64)
        self.assertTrue(all(x["retrieval_attribution"]=="UNDETERMINED" for x in r["records"]))
    def test_does_not_infer_gate_fault(self):
        r=diagnose(self.sample())["records"][0]
        self.assertEqual(r["gate_attribution"],"UNDETERMINED")
        self.assertIsNone(r["human_review"]["relevant"])
    def test_capture_alignment(self):
        doc=self.sample()
        cap={"groups":[{"id":f"A{i:02d}","turns":[{"question":str(i),"response":"答え","gate":"[gate=KNOWN, resolution=ACCEPT, reason=normal]"}]} for i in range(1,65)]}
        r=diagnose(doc,cap)
        self.assertEqual(r["with_gate_log"],64)
    def test_mismatch_rejected(self):
        doc=self.sample()
        cap={"groups":[{"id":f"A{i:02d}","turns":[{"question":"different","response":"答え"}]} for i in range(1,65)]}
        with self.assertRaises(ValueError):diagnose(doc,cap)
    def test_duplicate_rejected(self):
        doc=self.sample();doc["records"][1]["id"]="A01"
        with self.assertRaises(ValueError):diagnose(doc)
if __name__=="__main__":unittest.main()
