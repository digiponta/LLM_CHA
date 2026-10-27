import json
import tempfile
import unittest
from pathlib import Path
from prepare_unapproved_mention_qa_v01315 import prepare, mention_qa

class MentionQATests(unittest.TestCase):
    def test_mention_is_not_definition(self):
        row={"knowledge_id":"a","source_text":"運動には時間と空間が関係する。","source":"corpus"}
        item=mention_qa(row,"時間","UNAPPROVED")
        self.assertEqual(item["source_text"],row["source_text"])
        self.assertEqual(item["derivation"],"MENTION_ONLY_NOT_DEFINITION")
        self.assertEqual(item["truth_state"],"UNVERIFIED")
        self.assertIn("未承認",item["assistant"])
    def test_missing_term_no_qa(self):
        self.assertIsNone(mention_qa({"knowledge_id":"x","source_text":"物体が移動する。"},"始まり","UNAPPROVED"))
    def test_all_terms_and_rejection(self):
        with tempfile.TemporaryDirectory() as d:
            q=Path(d)/"q.jsonl"; l=Path(d)/"l.jsonl"
            rows=[{"knowledge_id":"a","source_text":"始まりと時間と空間。"},
                  {"knowledge_id":"b","source_text":"空間は別の話。"}]
            q.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in rows),encoding="utf-8")
            l.write_text(json.dumps({"knowledge_id":"b","approval_state":"REJECTED"},ensure_ascii=False)+"\n",encoding="utf-8")
            result=prepare(q,l,("始まり","時間","空間"),100)
            self.assertEqual(len(result),3)
            self.assertEqual(len({r["knowledge_id"] for r in result}),1)
            self.assertTrue(all(r["knowledge_id"]=="a" for r in result))
    def test_limit(self):
        with tempfile.TemporaryDirectory() as d:
            q=Path(d)/"q.jsonl";l=Path(d)/"l.jsonl"
            q.write_text(json.dumps({"knowledge_id":"a","source_text":"始まりと時間と空間。"},ensure_ascii=False)+"\n",encoding="utf-8")
            self.assertEqual(len(prepare(q,l,("始まり","時間","空間"),2)),2)

if __name__=="__main__":unittest.main()
