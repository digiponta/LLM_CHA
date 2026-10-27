import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from train_stratified_unapproved_qa_v01318 import build, binding_report

class StratifiedTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        d=Path(self.tmp.name)
        self.l1=d/"l1.jsonl";self.l2=d/"l2.jsonl"
        self.ledger=d/"ledger.jsonl";self.checkpoint=d/"base.pt"
        self.l1.write_text("",encoding="utf-8")
    def tearDown(self):
        self.tmp.cleanup()
    def save(self,path,rows):
        path.write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in rows),encoding="utf-8")
    @patch("train_stratified_unapproved_qa_v01318.checkpoint_trained_fingerprints",return_value=set())
    def test_all_three_subjects(self,_):
        self.save(self.l2,[{"knowledge_id":x,"subject":x,"user":f"Q{x}","assistant":f"A{x}"} for x in ("始まり","時間","空間")])
        rows=build(self.l1,self.l2,self.ledger,self.checkpoint,limit=3)
        self.assertEqual({r["subject"] for r in rows},{"始まり","時間","空間"})
        self.assertTrue(all(r["approval_state"]=="UNAPPROVED" for r in rows))
    @patch("train_stratified_unapproved_qa_v01318.checkpoint_trained_fingerprints",return_value=set())
    def test_rejection_blocks_subject(self,_):
        self.save(self.l2,[{"knowledge_id":"a","subject":"始まり","user":"Q","assistant":"A"}])
        self.save(self.ledger,[{"knowledge_id":"a","approval_state":"REJECTED"}])
        with self.assertRaisesRegex(ValueError,"NO_UNTRAINED_QA_FOR_SUBJECT"):
            build(self.l1,self.l2,self.ledger,self.checkpoint,limit=3)
    @patch("train_stratified_unapproved_qa_v01318.checkpoint_trained_fingerprints",return_value={"trained"})
    def test_binding_is_evidence_not_approval(self,_):
        row={"knowledge_id":"a","subject":"時間","pair_fingerprint":"trained",
             "approval_state":"UNAPPROVED","truth_state":"UNVERIFIED"}
        result=binding_report([row],self.checkpoint)[0]
        self.assertTrue(result["checkpoint_bound"])
        self.assertEqual(result["approval_state"],"UNAPPROVED")
        self.assertEqual(result["truth_state"],"UNVERIFIED")

if __name__=="__main__":unittest.main()
