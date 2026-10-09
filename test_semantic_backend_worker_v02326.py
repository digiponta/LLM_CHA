import argparse,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from evidence_dialogue_state_v02319 import DialogueState
from staged_semantic_internalization_v02325 import handle,approve,read_memory,training_queue
from semantic_backend_worker_v02326 import make_pair,run

class BackendWorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.mem=str(Path(self.tmp.name)/"memory.jsonl")
        _,out=handle(DialogueState(),"LLMを勉強したい",self.mem)
        self.key=out["record_id"]
    def tearDown(self):self.tmp.cleanup()
    def test_review_gate(self):
        record=read_memory(self.mem)[self.key]
        with self.assertRaises(ValueError):make_pair(record)
        self.assertEqual(training_queue(self.mem),[])
    def test_approved_pair_matches_short_training_prompt(self):
        approve(self.mem,self.key,"LLMの基本構造から学びましょう。")
        pair=make_pair(read_memory(self.mem)[self.key])
        self.assertIn("話題: LLM",pair["prompt"])
        self.assertIn("目的: 学習",pair["prompt"])
        self.assertTrue(pair["prompt"].endswith("AI: "))
        self.assertEqual(pair["answer"],"LLMの基本構造から学びましょう。")
    def test_no_queue_refuses(self):
        args=argparse.Namespace(memory=self.mem,epochs=1,lr=5e-6,head_lr=1e-6,replay_weight=.25)
        with self.assertRaisesRegex(ValueError,"No approved"):run(args)
    def test_plan_purpose_mapping(self):
        _,result=handle(DialogueState(),"LLMを勉強してから開発したい",self.mem)
        approve(self.mem,result["record_id"],"まず基礎を学び、次に試作品を開発します。")
        pair=make_pair(read_memory(self.mem)[result["record_id"]])
        self.assertIn("目的: 学習 → 開発",pair["prompt"])

if __name__=="__main__":unittest.main()
