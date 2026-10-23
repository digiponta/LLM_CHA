import ast
import tempfile
import unittest
from pathlib import Path
import torch
from dual_semantic_memory_v071 import DualMemory
from experimental_reload_v0723 import reload_after_sleep

class FakeBackend:
    def __init__(self,base,tokenizer,adapter):
        self.adapter_path=adapter
    def __call__(self,question):
        return "probe"

class ReloadTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        root=Path(self.tmp.name)
        self.approved=root/"approved.jsonl"
        self.candidates=root/"candidates.jsonl"
        self.memory=DualMemory(self.approved,self.candidates)
        self.memory.propose("青い鍵の符号は何ですか","AO-17","test")
        self.ids=[r["id"] for r in self.memory.candidates()]
        self.ckpt=root/"adapter.pt"
        self.old=object()
    def tearDown(self):self.tmp.cleanup()
    def save(self,**overrides):
        c={"route":"experimental","approved":False,
           "candidate_ids":self.ids,"rank":16,"base_hash":"dummy",
           "adapter":{"a":torch.ones(1)}}
        c.update(overrides)
        torch.save(c,self.ckpt)
    def reload(self,status="TRAINED"):
        return reload_after_sleep(
            {"status":status,"checkpoint":str(self.ckpt)},
            self.approved,self.candidates,"base.pt","tokenizer.json",self.old,
            backend_class=FakeBackend)
    def test_load(self):
        self.save()
        backend,info=self.reload()
        self.assertIsInstance(backend,FakeBackend)
        self.assertEqual(info["status"],"LOADED")
    def test_wrong_route_rejected(self):
        self.save(route="trusted")
        backend,info=self.reload()
        self.assertIs(backend,self.old)
        self.assertEqual(info["status"],"REJECTED")
    def test_candidate_mismatch_rejected(self):
        self.save(candidate_ids=["other"])
        backend,info=self.reload()
        self.assertIs(backend,self.old)
        self.assertEqual(info["status"],"REJECTED")
    def test_unapproved_flag_rejected(self):
        self.save(approved=True)
        backend,info=self.reload()
        self.assertEqual(info["status"],"REJECTED")
        self.assertIs(backend,self.old)
    def test_no_pending_stays(self):
        backend,info=self.reload(status="NO_PENDING")
        self.assertIs(backend,self.old)
        self.assertEqual(info["status"],"UNCHANGED")
    def test_corrupt_checkpoint_rejected(self):
        self.ckpt.write_bytes(b"not a pytorch file")
        backend,info=self.reload()
        self.assertIs(backend,self.old)
        self.assertEqual(info["status"],"REJECTED")
    def test_chat_wiring(self):
        s=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        ast.parse(s)
        self.assertIn("memory_first_generator, reload_info = reload_after_sleep(",s)
if __name__=="__main__":unittest.main()
