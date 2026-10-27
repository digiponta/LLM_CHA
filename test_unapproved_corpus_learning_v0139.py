import json
import tempfile
import unittest
from pathlib import Path
from unapproved_corpus_learning_v0139 import corpus_rows, plan

class UnapprovedCorpusTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        d=Path(self.tmp.name)
        self.source=d/"data-nagato.txt"
        self.ledger=d/"ledger.jsonl"
        self.queue=d/"queue.jsonl"
        self.source.write_text(
            "始まりには説明がある。時間と空間について考える。\n"
            "重力は仮説として述べられている。",encoding="utf-8")
    def tearDown(self):
        self.tmp.cleanup()
    def test_subject_independent_coverage(self):
        rows=corpus_rows(self.source)
        self.assertEqual(len(rows),3)
        self.assertTrue(any("時間と空間" in row["source_text"] for row in rows))
        self.assertTrue(all(row["approval_state"]=="UNAPPROVED" for row in rows))
    def test_readonly_status(self):
        result=plan(self.source,self.ledger,self.queue,limit=2)
        self.assertEqual(result["batch"],2)
        self.assertFalse(self.ledger.exists())
        self.assertFalse(self.queue.exists())
    def test_deduplicated_batches(self):
        plan(self.source,self.ledger,self.queue,limit=2,write=True)
        self.assertEqual(plan(self.source,self.ledger,self.queue,limit=2,write=True)["batch"],1)
        self.assertEqual(plan(self.source,self.ledger,self.queue,limit=2,write=True)["batch"],0)
        self.assertEqual(len(self.queue.read_text(encoding="utf-8").splitlines()),3)
    def test_rejected_not_enqueued(self):
        rows=corpus_rows(self.source)
        self.ledger.write_text(json.dumps({**rows[0],"approval_state":"REJECTED"},ensure_ascii=False)+"\n",encoding="utf-8")
        result=plan(self.source,self.ledger,self.queue,limit=10,write=True)
        self.assertEqual(result["rejected"],1)
        self.assertEqual(result["batch"],2)
        self.assertNotIn(rows[0]["knowledge_id"],self.queue.read_text(encoding="utf-8"))
    def test_approved_state_preserved(self):
        rows=corpus_rows(self.source)
        self.ledger.write_text(json.dumps({**rows[0],"approval_state":"APPROVED"},ensure_ascii=False)+"\n",encoding="utf-8")
        result=plan(self.source,self.ledger,self.queue,limit=1,write=True)
        self.assertEqual(result["approved"],1)
    def test_training_not_claimed(self):
        plan(self.source,self.ledger,self.queue,limit=2,write=True)
        rows=[json.loads(x) for x in self.queue.read_text(encoding="utf-8").splitlines()]
        self.assertTrue(all(r["training_state"]=="PENDING" for r in rows))
        self.assertTrue(all(r["truth_state"]=="UNVERIFIED" for r in rows))

if __name__=="__main__":unittest.main()
