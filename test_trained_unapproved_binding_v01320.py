import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from online_train import pair_fingerprint
from trained_unapproved_binding_v01320 import lookup, format_quotation

class TrainedUnapprovedTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        d=Path(self.t.name)
        self.checkpoint=d/"model.pt";self.checkpoint.write_bytes(b"test")
        self.qa=d/"qa.jsonl";self.ledger=d/"ledger.jsonl"
        self.row={"knowledge_id":"raw-a","subject":"時間",
                  "user":"未承認の原文で「時間」に言及した文章を示してください。",
                  "assistant":"【未承認の記録・事実未検証】時間を含む文章。",
                  "source_text":"時間を含む文章。","approval_state":"UNAPPROVED",
                  "truth_state":"UNVERIFIED"}
        self.qa.write_text(json.dumps(self.row,ensure_ascii=False)+"\n",encoding="utf-8")
        self.fp=pair_fingerprint(self.row["user"],self.row["assistant"])
    def tearDown(self):self.t.cleanup()
    def look(self,**kw):
        return lookup("時間",self.checkpoint,self.ledger,(self.qa,),**kw)
    @patch("trained_unapproved_binding_v01320.checkpoint_trained_fingerprints")
    def test_checkpoint_bound_quote(self,fp):
        fp.return_value={self.fp}
        result=self.look()
        self.assertEqual(result["state"],"TRAINED_UNAPPROVED")
        self.assertIn("未承認",format_quotation(result))
    @patch("trained_unapproved_binding_v01320.checkpoint_trained_fingerprints",return_value=set())
    def test_not_trained_blocked(self,_):self.assertIsNone(self.look())
    @patch("trained_unapproved_binding_v01320.checkpoint_trained_fingerprints")
    def test_rejected_blocked(self,fp):
        fp.return_value={self.fp}
        self.ledger.write_text(json.dumps({"knowledge_id":"raw-a","approval_state":"REJECTED"})+"\n",encoding="utf-8")
        self.assertIsNone(self.look())
    @patch("trained_unapproved_binding_v01320.checkpoint_trained_fingerprints")
    def test_truth_block(self,fp):
        fp.return_value={self.fp}
        self.assertIsNone(self.look(truth_block=True))
    @patch("trained_unapproved_binding_v01320.checkpoint_trained_fingerprints")
    def test_subject_is_exact(self,fp):
        fp.return_value={self.fp}
        self.assertIsNone(lookup("空間",self.checkpoint,self.ledger,(self.qa,)))

if __name__=="__main__":unittest.main()
