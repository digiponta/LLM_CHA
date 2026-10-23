import json,tempfile,unittest
from pathlib import Path
from dual_semantic_memory_v071 import DualMemory
from experimental_memory_first_v0720 import memory_first

class MemoryFirstTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        p=Path(self.temp.name)
        self.memory=DualMemory(p/"approved.jsonl",p/"candidates.jsonl")
        self.memory.propose("青い鍵の符号は何ですか","AO-17","synthetic:test")
        self.memory.propose("赤い橋の符号は何ですか","RB-42","synthetic:test")
    def tearDown(self):self.temp.cleanup()
    def unknown(self,q):return {"status":"UNKNOWN"}
    def test_evidence(self):
        r=memory_first("青い鍵の符号を教えて",self.memory,trusted_ask=self.unknown,enabled=True)
        self.assertEqual(r["answer"],"【未承認・候補知識】AO-17")
        self.assertEqual(r["truth_state"],"EXPERIMENTAL_UNVERIFIED")
    def test_mismatched_generation_cannot_override(self):
        r=memory_first("赤い橋の符号を教えて",self.memory,trusted_ask=self.unknown,
            experimental_generate=lambda p:"WRONG",enabled=True,mode="constrained")
        self.assertEqual(r["answer"],"【未承認・候補知識】RB-42")
        self.assertFalse(r["generation_consistent"])
        self.assertFalse(r["auto_promote"])
    def test_consistent_generation(self):
        r=memory_first("赤い橋の符号を教えて",self.memory,trusted_ask=self.unknown,
            experimental_generate=lambda p:"RB-42",enabled=True,mode="constrained")
        self.assertTrue(r["generation_consistent"])
    def test_trusted_precedes_experimental(self):
        def fail(p):raise AssertionError("experimental was called")
        r=memory_first("青い鍵の符号を教えて",self.memory,
            trusted_ask=lambda q:{"status":"ANSWER","answer":"承認済みです。"},
            experimental_generate=fail,enabled=True,mode="constrained")
        self.assertEqual(r["route"],"TRUSTED")
    def test_disabled(self):
        r=memory_first("青い鍵の符号を教えて",self.memory,trusted_ask=self.unknown)
        self.assertEqual(r["route"],"TRUSTED_UNKNOWN")
    def test_unknown_no_generator(self):
        def fail(p):raise AssertionError("experimental was called")
        r=memory_first("紫の窓の符号を教えて",self.memory,trusted_ask=self.unknown,
            experimental_generate=fail,enabled=True,mode="constrained")
        self.assertEqual(r["route"],"EXPERIMENTAL_UNKNOWN")
    def test_invalid_trusted_status(self):
        with self.assertRaises(ValueError):
            memory_first("青い鍵",self.memory,trusted_ask=lambda q:{"status":"REVIEW"},enabled=True)
    def test_empty_trusted_answer(self):
        with self.assertRaises(ValueError):
            memory_first("青い鍵",self.memory,trusted_ask=lambda q:{"status":"ANSWER","answer":""},enabled=True)
if __name__=="__main__":unittest.main()
