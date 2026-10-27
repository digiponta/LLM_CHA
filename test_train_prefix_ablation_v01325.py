import json
import tempfile
import unittest
from pathlib import Path
from train_prefix_ablation_v01325 import strip_label, transform, prepare

class PrefixAblationTests(unittest.TestCase):
    def setUp(self):
        self.row={"user":"時間について","assistant":"【未承認の記録・事実未検証】時間についての原文。",
                  "knowledge_id":"k1","subject":"時間"}
    def test_strip(self):
        self.assertEqual(strip_label(self.row["assistant"]),"時間についての原文。")
    def test_raw(self):
        result=transform(self.row,"B_RAW")
        self.assertEqual(result["assistant"],"時間についての原文。")
        self.assertEqual(result["approval_state"],"UNAPPROVED")
    def test_label(self):
        self.assertEqual(transform(self.row,"A_LABEL")["assistant"],self.row["assistant"])
    def test_natural(self):
        self.assertEqual(transform(self.row,"D_NATURAL")["assistant"],"原文では、時間についての原文。")
    def test_rejected_excluded(self):
        with tempfile.TemporaryDirectory() as d:
            ledger=Path(d)/"ledger.jsonl"
            ledger.write_text(json.dumps({"knowledge_id":"k1","approval_state":"REJECTED"})+"\n",encoding="utf-8")
            result=prepare([self.row],ledger,16)
            self.assertTrue(all(not rows for rows in result.values()))
    def test_same_question(self):
        rows=[transform(self.row,k) for k in ("A_LABEL","B_RAW","D_NATURAL")]
        self.assertEqual(len({x["user"] for x in rows}),1)
        self.assertEqual(len({x["assistant"] for x in rows}),3)

if __name__=="__main__":unittest.main()
