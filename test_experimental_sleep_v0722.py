import ast
import tempfile
import unittest
from pathlib import Path
from dual_semantic_memory_v071 import DualMemory
from experimental_sleep_v0722 import experimental_sleep

class ExperimentalSleepTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.approved=self.root/"approved.jsonl"
        self.candidates=self.root/"candidates.jsonl"
        self.memory=DualMemory(self.approved,self.candidates)
        self.calls=[]
    def tearDown(self):self.temp.cleanup()
    def trainer(self,base,tokenizer,approved,candidates,destination,**kw):
        self.calls.append((base,tokenizer,approved,candidates,str(destination),kw))
        import torch
        records=DualMemory(approved,candidates).candidates()
        destination.parent.mkdir(parents=True,exist_ok=True)
        torch.save({"route":"experimental","approved":False,
                    "candidate_ids":[r["id"] for r in records]},destination)
        return {"pass":True}
    def sleep(self):
        return experimental_sleep(self.approved,self.candidates,
            self.root/"base.pt",self.root/"tokenizer.json",self.root/"output",
            trainer=self.trainer)
    def test_no_pending_never_trains(self):
        r=self.sleep()
        self.assertEqual(r["status"],"NO_PENDING")
        self.assertFalse(self.calls)
    def test_pending_only_trains(self):
        self.memory.propose("質問A","答A","synthetic")
        r=self.sleep()
        self.assertEqual(r["status"],"TRAINED")
        self.assertEqual(len(self.calls),1)
        self.assertEqual(r["pending"],1)
        self.assertFalse(r["auto_promote"])
        self.assertFalse(r["trusted_changed"])
        self.assertFalse(self.memory.approved())
    def test_repeated_sleep_is_idempotent(self):
        self.memory.propose("質問A","答A","synthetic")
        self.sleep()
        r=self.sleep()
        self.assertEqual(r["status"],"ALREADY_TRAINED")
        self.assertEqual(len(self.calls),1)
    def test_additional_candidate_new_checkpoint(self):
        self.memory.propose("質問A","答A","synthetic")
        self.sleep()
        self.memory.propose("質問B","答B","synthetic")
        r=self.sleep()
        self.assertEqual(r["pending"],2)
        self.assertEqual(len(self.calls),2)
    def test_chat_wiring(self):
        source=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn('if command == "/sleep":',source)
        self.assertIn("experimental_sleep_result = experimental_sleep(",source)

if __name__=="__main__":unittest.main()
