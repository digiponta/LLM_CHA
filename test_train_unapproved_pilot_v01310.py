import json
import tempfile
import unittest
from pathlib import Path
from train_unapproved_pilot_v01310 import build_batch

class UnapprovedPilotTests(unittest.TestCase):
    def test_ledger_rejection_overrides_stale_queue(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            queue=root/"queue.jsonl";ledger=root/"ledger.jsonl"
            items=[
                {"knowledge_id":"a","source_text":"始まりには複数の説明がある。","training_state":"PENDING","approval_state":"UNAPPROVED"},
                {"knowledge_id":"b","source_text":"時間と空間には関係がある。","training_state":"PENDING","approval_state":"UNAPPROVED"},
            ]
            queue.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in items),encoding="utf-8")
            ledger.write_text(json.dumps({"knowledge_id":"a","approval_state":"REJECTED"},ensure_ascii=False)+"\n",encoding="utf-8")
            batch=build_batch(queue,ledger,16)
            self.assertEqual(len(batch),1)
            self.assertEqual(batch[0]["knowledge_id"],"b")
            self.assertEqual(batch[0]["source"],"corpus-unapproved")
            self.assertEqual(batch[0]["truth_state"],"UNVERIFIED")
            self.assertEqual(batch[0]["assistant"],items[1]["source_text"])
    def test_batch_size_limit(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); queue=root/"queue.jsonl"; ledger=root/"ledger.jsonl"
            queue.write_text("".join(json.dumps({"knowledge_id":str(i),"source_text":f"文章{i}。",
                "training_state":"PENDING"},ensure_ascii=False)+"\n" for i in range(10)),encoding="utf-8")
            self.assertEqual(len(build_batch(queue,ledger,3)),3)
    def test_completed_not_selected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); queue=root/"queue.jsonl"; ledger=root/"ledger.jsonl"
            queue.write_text(json.dumps({"knowledge_id":"x","source_text":"以前の文章","training_state":"TRAINED"})+"\n",encoding="utf-8")
            self.assertEqual(build_batch(queue,ledger,5),[])

if __name__=="__main__":unittest.main()
