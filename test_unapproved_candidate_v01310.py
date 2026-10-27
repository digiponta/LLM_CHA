import json
import tempfile
import unittest
from pathlib import Path
from train_unapproved_candidate_v01310 import build_batch

class CandidateTrainingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.queue=self.root/"queue.jsonl"
        self.ledger=self.root/"ledger.jsonl"
        self.batch=self.root/"batch.jsonl"
        self.rows=[
            {"knowledge_id":"a","source_text":"時間と空間には関連があると書かれている。","training_state":"PENDING","approval_state":"UNAPPROVED"},
            {"knowledge_id":"b","source_text":"始まりという概念を説明する原文です。","training_state":"PENDING","approval_state":"UNAPPROVED"},
            {"knowledge_id":"c","source_text":"却下した文章は学習しないようにする。","training_state":"PENDING","approval_state":"UNAPPROVED"},
        ]
        self.queue.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in self.rows),encoding="utf-8")
        self.ledger.write_text(json.dumps({"knowledge_id":"c","approval_state":"REJECTED"})+"\n",encoding="utf-8")
    def tearDown(self):self.tmp.cleanup()
    def test_stages_unapproved_only(self):
        rows=build_batch(self.queue,self.ledger,self.batch,limit=8)
        self.assertEqual(len(rows),2)
        self.assertTrue(all(x["source"]=="corpus-unapproved" for x in rows))
    def test_rejected_excluded(self):
        self.assertNotIn("c",[x["knowledge_id"] for x in build_batch(self.queue,self.ledger,None)])
    def test_no_approval_promotion(self):
        build_batch(self.queue,self.ledger,self.batch)
        self.assertIn('"REJECTED"',self.ledger.read_text(encoding="utf-8"))
        self.assertTrue(all(x["truth_state"]=="UNVERIFIED" for x in json.loads(line) for line in [])) if False else None
        self.assertTrue(all(json.loads(x)["truth_state"]=="UNVERIFIED" for x in self.batch.read_text(encoding="utf-8").splitlines()))
    def test_bounded_batch(self):
        self.assertEqual(len(build_batch(self.queue,self.ledger,None,limit=1)),1)
        with self.assertRaises(ValueError):build_batch(self.queue,self.ledger,None,limit=101)
    def test_no_checkpoint_written(self):
        build_batch(self.queue,self.ledger,self.batch)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()),["batch.jsonl","ledger.jsonl","queue.jsonl"])

if __name__=="__main__":unittest.main()
