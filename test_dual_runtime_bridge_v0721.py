import ast
import tempfile
import unittest
from pathlib import Path
from dual_semantic_memory_v071 import DualMemory
from dual_runtime_bridge_v0721 import resolve

class RuntimeBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        root=Path(self.temp.name)
        self.approved=root/"approved.jsonl"
        self.candidates=root/"candidates.jsonl"
        self.mem=DualMemory(self.approved,self.candidates)
        self.mem.propose("青い鍵の符号は何ですか","AO-17","synthetic")
    def tearDown(self):self.temp.cleanup()
    def route(self,q,**kw):
        return resolve(q,self.approved,self.candidates,enabled=True,**kw)
    def test_evidence_unverified(self):
        x=self.route("青い鍵の符号を教えて")
        self.assertEqual(x["truth_state"],"EXPERIMENTAL_UNVERIFIED")
        self.assertEqual(x["reason"],"candidate_evidence")
        self.assertFalse(x["auto_promote"])
    def test_disabled(self):
        self.assertIsNone(resolve("青い鍵",self.approved,self.candidates,enabled=False))
    def test_trust_block(self):
        self.assertIsNone(self.route("青い鍵",resolution="TRUTH_BLOCK"))
    def test_unknown(self):
        x=self.route("紫の窓の符号は何ですか")
        self.assertEqual(x["truth_state"],"UNKNOWN")
    def test_generation_mismatch_contains(self):
        x=self.route("青い鍵の符号を教えて",mode="constrained",
                     generator=lambda p:"WRONG")
        self.assertEqual(x["generation_status"],"REJECTED_TO_EVIDENCE")
        self.assertEqual(x["answer"],"【未承認・候補知識】AO-17")
    def test_chat_syntax(self):
        ast.parse(Path(__file__).with_name("chat.py").read_text(encoding="utf-8"))
    def test_optin_gate_wiring(self):
        code=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        self.assertIn("LLM_CHA_MEMORY_FIRST",code)
        self.assertIn('resolution_name == "UNKNOWN_KNOWLEDGE" and memory_first_enabled',code)
        self.assertIn('reason == "low response agreement"',code)
if __name__=="__main__":unittest.main()
