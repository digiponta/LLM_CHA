import json
import tempfile
import unittest
from pathlib import Path
from prepare_unapproved_b_raw_v01326 import convert, POLICY

class BRawAdoptionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.ledger=Path(self.temp.name)/"ledger.jsonl"
    def tearDown(self):self.temp.cleanup()
    def test_default(self):self.assertEqual(POLICY,"B_RAW")
    def test_removes_label_and_preserves_identity(self):
        row={"knowledge_id":"k1","user":"時間について","assistant":"【未承認の記録・事実未検証】原文。",
             "source_text":"原文。","subject":"時間"}
        out=convert([row],self.ledger)
        self.assertEqual(out[0]["assistant"],"原文。")
        self.assertEqual(out[0]["knowledge_id"],"k1")
        self.assertEqual(out[0]["approval_state"],"UNAPPROVED")
        self.assertEqual(out[0]["truth_state"],"UNVERIFIED")
    def test_rejected_and_approved_not_trainable(self):
        self.ledger.write_text('{"knowledge_id":"k1","approval_state":"REJECTED"}\n'+
                               '{"knowledge_id":"k2","approval_state":"APPROVED"}\n',encoding="utf-8")
        rows=[{"knowledge_id":k,"user":"問","assistant":"答"} for k in ("k1","k2")]
        self.assertEqual(convert(rows,self.ledger),[])
    def test_fallback_to_legacy_answer(self):
        rows=[{"knowledge_id":"k3","user":"問","assistant":"【未承認の記録】引用文。"}]
        self.assertEqual(convert(rows,self.ledger)[0]["assistant"],"引用文。")

if __name__=="__main__":unittest.main()
