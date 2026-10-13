"""Synthetic regression tests for v0.4.28.9 observability."""
import unittest
from runtime_stage_observability_v04289 import gate_fields,observe
class Tests(unittest.TestCase):
    def fixture(self):
        groups=[]
        for cat,n in (("A",12),("B",12),("C",8),("D",8),("E",8),("G",4)):
            for i in range(1,n+1):
                groups.append({"id":f"{cat}{i:02d}","status":"FINISHED","turns":[
                    {"question":"質問","response":"回答","gate":"[gate=KNOWN, confidence=0.9, resolution=ACCEPT, reason=normal]"}]})
        for i in range(1,5):
            groups.append({"id":f"F{i}","status":"FINISHED","turns":[
                {"question":"質問","response":"回答","gate":None} for _ in range(3)]})
        return {"groups":groups}
    def test_metrics(self):
        x=gate_fields("[gate=UNKNOWN, confidence=0.477, agreement=0.000, sem_agreement=0.82, resolution=GATE_REVIEW]")
        self.assertAlmostEqual(x["metrics"]["confidence"],0.477)
        self.assertAlmostEqual(x["metrics"]["sem_agreement"],0.82)
        self.assertEqual(x["fields"]["resolution"],"GATE_REVIEW")
    def test_no_fake_retrieval(self):
        r=observe(self.fixture())
        self.assertEqual(r["total_turns"],64)
        self.assertEqual(r["retrieval_observed"],0)
        self.assertEqual(r["pre_gate_generation_observed"],0)
        self.assertFalse(r["runtime_instrumented"])
    def test_gate_counts(self):
        r=observe(self.fixture())
        self.assertEqual(r["gate_observed"],52)
        self.assertEqual(r["gate_metrics_observed"],52)
    def test_missing_gate(self):
        self.assertFalse(gate_fields(None)["observed"])
    def test_bad_shape(self):
        d=self.fixture();d["groups"].pop()
        with self.assertRaises(ValueError):observe(d)
if __name__=="__main__":unittest.main()
