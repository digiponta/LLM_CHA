import json
import tempfile
import unittest
from pathlib import Path
from train_combined_unapproved_qa_v01316 import combine

class CombinedQATests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        d=Path(self.temp.name)
        self.l1=d/"l1.jsonl";self.l2=d/"l2.jsonl";self.ledger=d/"ledger.jsonl"
    def tearDown(self):
        self.temp.cleanup()
    def save(self,path,rows):
        path.write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in rows),encoding="utf-8")
    def test_balanced_interleaving(self):
        self.save(self.l1,[{"knowledge_id":"a","user":"Q1","assistant":"A1","derivation":"EXPLICIT_SUBJECT_ONLY"},
                           {"knowledge_id":"b","user":"Q2","assistant":"A2","derivation":"EXPLICIT_SUBJECT_ONLY"}])
        self.save(self.l2,[{"knowledge_id":"c","user":"Q3","assistant":"A3","derivation":"MENTION_ONLY_NOT_DEFINITION"}])
        result=combine(self.l1,self.l2,self.ledger,3)
        self.assertEqual([r["knowledge_id"] for r in result],["a","c","b"])
    def test_rejected_filtered(self):
        self.save(self.l1,[{"knowledge_id":"a","user":"Q","assistant":"A"}])
        self.save(self.l2,[])
        self.save(self.ledger,[{"knowledge_id":"a","approval_state":"REJECTED"}])
        self.assertEqual(combine(self.l1,self.l2,self.ledger,10),[])
    def test_duplicate_pair_removed(self):
        row={"knowledge_id":"a","user":"Q","assistant":"A"}
        self.save(self.l1,[row]);self.save(self.l2,[row])
        self.assertEqual(len(combine(self.l1,self.l2,self.ledger,10)),1)
    def test_unapproved_label_retained(self):
        self.save(self.l1,[{"knowledge_id":"a","user":"Q","assistant":"【未承認の記録】A"}])
        self.save(self.l2,[])
        result=combine(self.l1,self.l2,self.ledger,1)
        self.assertEqual(result[0]["truth_state"],"UNVERIFIED")
        self.assertEqual(result[0]["approval_state"],"UNAPPROVED")

if __name__=="__main__":unittest.main()
