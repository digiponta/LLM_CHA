import ast
import tempfile
import unittest
from pathlib import Path
import torch
from dual_semantic_memory_v071 import DualMemory
from experimental_restore_v0724 import restore_latest

class FakeBackend:
    def __init__(self,base,tokenizer,path):
        self.adapter_path=Path(path)
    def __call__(self,q):return "probe"

class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        root=Path(self.tmp.name)
        self.approved=root/"approved.jsonl"
        self.candidates=root/"candidates.jsonl"
        self.folder=root/"outputs"
        self.folder.mkdir()
        self.memory=DualMemory(self.approved,self.candidates)
        self.memory.propose("青い鍵の符号は何ですか","AO-17","test")
        self.ids=[r["id"] for r in self.memory.candidates()]
    def tearDown(self):self.tmp.cleanup()
    def checkpoint(self,name,ids=None,route="experimental"):
        file=self.folder/name
        torch.save({"route":route,"approved":False,"rank":16,
                    "candidate_ids":self.ids if ids is None else ids,
                    "base_hash":"test","adapter":{"a":torch.ones(1)}},file)
        return file
    def restore(self):
        return restore_latest(self.folder,self.approved,self.candidates,
                              "base.pt","tok.json",backend_class=FakeBackend)
    def test_restore_valid(self):
        valid=self.checkpoint("experimental-sleep-one.pt")
        b,r=self.restore()
        self.assertEqual(r["status"],"RESTORED")
        self.assertEqual(b.adapter_path,valid)
    def test_reject_mismatched_candidates(self):
        self.checkpoint("experimental-sleep-stale.pt",ids=["stale"])
        b,r=self.restore()
        self.assertIsNone(b)
        self.assertEqual(r["status"],"NO_VALID_CHECKPOINT")
    def test_reject_invalid_route(self):
        self.checkpoint("experimental-sleep-invalid.pt",route="trusted")
        b,r=self.restore()
        self.assertIsNone(b)
        self.assertEqual(r["status"],"NO_VALID_CHECKPOINT")
    def test_no_checkpoint(self):
        b,r=self.restore()
        self.assertEqual(r["status"],"NO_CHECKPOINT")
    def test_ignore_invalid_and_select_valid(self):
        valid=self.checkpoint("experimental-sleep-valid.pt")
        corrupted=self.folder/"experimental-sleep-invalid.pt"
        corrupted.write_bytes(b"invalid")
        b,r=self.restore()
        self.assertEqual(r["status"],"RESTORED")
        self.assertEqual(b.adapter_path,valid)
    def test_added_candidate_rejects_old(self):
        self.checkpoint("experimental-sleep-old.pt")
        self.memory.propose("赤い橋の符号は何ですか","RB-42","test")
        b,r=self.restore()
        self.assertEqual(r["status"],"NO_VALID_CHECKPOINT")
    def test_chat_startup_integration(self):
        source=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("[experimental startup restore:",source)
if __name__=="__main__":unittest.main()
