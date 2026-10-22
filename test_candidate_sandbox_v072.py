import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from dual_semantic_memory_v071 import DualMemory
from candidate_sandbox_train_v072 import select_candidates,run,commands_for_training

class SandboxTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        p=Path(self.tmp.name)
        self.root=p
        self.mem=DualMemory(p/"approved.jsonl",p/"candidates.jsonl")
    def tearDown(self):self.tmp.cleanup()
    def test_only_pending(self):
        x=self.mem.propose("問いA","回答A","candidate:a")
        y=self.mem.propose("問いB","回答B","candidate:b")
        self.mem.reject(y)
        self.assertEqual([r["id"] for r in select_candidates(self.mem)],[x])
    def test_approved_excluded(self):
        x=self.mem.propose("問いA","回答A","source-a")
        self.mem.approve(x)
        self.assertEqual(select_candidates(self.mem),[])
    def test_conflicting_candidates(self):
        self.mem.propose("問い","答えA","a")
        self.mem.propose("問い","答えB","b")
        with self.assertRaises(ValueError):select_candidates(self.mem)
    def test_sandbox_flags_disable_replay(self):
        args=commands_for_training("online_train.py",Path("base"),Path("tok"),Path("tmp/pairs"),
            Path("state"),Path("output"),3,3e-6)
        self.assertEqual(args[args.index("--stability-weight")+1],"0")
        self.assertEqual(args[args.index("--replay-ratio")+1],"0")
    def test_no_protected_changes(self):
        self.mem.propose("問い","候補回答","source:1")
        base=self.root/"base.pt"
        tok=self.root/"tokenizer.json"
        script=self.root/"trainer.py"
        for p in (base,tok,script):p.write_text("unchanged",encoding="utf-8")
        class Result:
            returncode=1
            stdout=""
            stderr="mock failure"
        with patch("candidate_sandbox_train_v072.subprocess.run",return_value=Result()):
            result=run(self.mem.approved_path,self.mem.candidate_path,base,tok,self.root/"sandbox",trainer=script)
        self.assertFalse(result["pass"])
        self.assertTrue(result["protected_sources_unchanged"])
        self.assertEqual(len(self.mem.candidates()),1)
        self.assertIsNone(self.mem.lookup_approved("問い"))
    def test_no_pending_rejected(self):
        with self.assertRaises(ValueError):
            run(self.mem.approved_path,self.mem.candidate_path,"missing","missing",self.root/"sandbox")
if __name__=="__main__":unittest.main()
