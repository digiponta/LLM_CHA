import json
import tempfile
import unittest
from pathlib import Path
from prepare_unapproved_semantic_qa_v01314 import grounded_qa, prepare

class GroundedQATests(unittest.TestCase):
    def test_explicit_subject_grounds_answer(self):
        item=grounded_qa({"knowledge_id":"k1","source_text":"重力は、物体の性質として記述される。"})
        self.assertIsNotNone(item)
        self.assertEqual(item["subject"],"重力")
        self.assertEqual(item["knowledge_id"],"k1")
        self.assertEqual(item["truth_state"],"UNVERIFIED")
        self.assertTrue(item["assistant"].startswith("【未承認の記録】"))
    def test_incidental_mention_not_definition(self):
        item=grounded_qa({"knowledge_id":"k2","source_text":"例えば、空間上の振動は、時間軸方向の振動も許容する。"})
        self.assertIsNone(item)
    def test_rejected_excluded_and_approved_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            q=Path(d)/"q.jsonl";l=Path(d)/"l.jsonl"
            rows=[{"knowledge_id":"a","source_text":"時間は、複数の観測に関係している。"},
                  {"knowledge_id":"b","source_text":"空間は、原文で説明されている。"}]
            q.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in rows),encoding="utf-8")
            l.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in
              [{"knowledge_id":"a","approval_state":"REJECTED"},
               {"knowledge_id":"b","approval_state":"APPROVED"}]),encoding="utf-8")
            result=prepare(q,l,10)
            self.assertEqual(len(result),1)
            self.assertEqual(result[0]["approval_state"],"APPROVED")
            self.assertEqual(result[0]["knowledge_id"],"b")
    def test_term_filter_exact(self):
        with tempfile.TemporaryDirectory() as d:
            q=Path(d)/"q.jsonl";l=Path(d)/"l.jsonl"
            q.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in
              [{"knowledge_id":"a","source_text":"時間は、状態の順序を表す。"},
               {"knowledge_id":"b","source_text":"空間は、対象を含んでいる。"}]),encoding="utf-8")
            result=prepare(q,l,10,("時間",))
            self.assertEqual([x["subject"] for x in result],["時間"])

if __name__=="__main__":
    unittest.main()
