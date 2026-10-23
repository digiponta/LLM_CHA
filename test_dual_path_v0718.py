import tempfile,unittest,json
from pathlib import Path
from dual_semantic_memory_v071 import DualMemory
from experimental_dual_path_v0718 import answer
from benchmark_dual_path_v0718 import evaluate

class DualPathTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        root=Path(self.tmp.name)
        self.mem=DualMemory(root/"approved.jsonl",root/"candidates.jsonl")
        self.id=self.mem.propose("青い鍵の符号は何ですか","AO-17","synthetic")
        self.rows=root/"holdouts.json"
        self.rows.write_text(json.dumps([{"question":"青い鍵の符号を教えて",
          "reference":"AO-17","candidate_id":self.id}],ensure_ascii=False),encoding="utf-8")
    def tearDown(self):self.tmp.cleanup()
    def test_evidence_mode_does_not_invoke_adapter(self):
        r=answer(self.mem,"青い鍵の符号を教えて",mode="evidence",
            backend=lambda q:1/0)
        self.assertEqual(r["truth_state"],"EXPERIMENTAL_UNVERIFIED")
        self.assertIn("AO-17",r["answer"])
    def test_adapter_exact(self):
        r=answer(self.mem,"青い鍵の符号を教えて",mode="adapter",
            backend=lambda q:"AO-17")
        self.assertEqual(r["route"],"EXPERIMENTAL_FALLBACK")
        self.assertFalse(r["auto_promote"])
    def test_adapter_mismatch_rejected(self):
        r=answer(self.mem,"青い鍵の符号を教えて",mode="adapter",
            backend=lambda q:"WB-26")
        self.assertEqual(r["route"],"EXPERIMENTAL_REJECTED")
    def test_missing_unapproved_not_generated(self):
        def fail(q):raise AssertionError("unexpected adapter call")
        r=answer(self.mem,"紫色の扉",mode="compare",backend=fail)
        self.assertEqual(r["truth_state"],"UNKNOWN")
    def test_optin(self):
        r=answer(self.mem,"青い鍵の符号を教えて",allow=False)
        self.assertEqual(r["route"],"EXPERIMENTAL_DISABLED")
    def test_side_by_side(self):
        r=evaluate(self.mem,self.rows,lambda q:"AO-17")
        self.assertEqual((r["retrieval_correct"],r["evidence_exact"],r["adapter_exact"]),(1,1,1))
        self.assertEqual(r["factual_verification"],"NOT_PERFORMED")
    def test_invalid_mode(self):
        with self.assertRaises(ValueError):answer(self.mem,"青い鍵",mode="production")
if __name__=="__main__":unittest.main()
