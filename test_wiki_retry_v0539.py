import ast
import unittest
from unittest.mock import patch
from pathlib import Path
from wiki_retry_v0539 import resolve_topic,retry
GOOD={"status":"FOUND","url":"https://ja.wikipedia.org/wiki/量子コンピュータ",
"extract":"量子コンピュータは量子力学の原理を利用した計算機である。詳細は後述。",
"title":"量子コンピュータ"}
class WikiRetryTests(unittest.TestCase):
 def test_topic(self):self.assertEqual(resolve_topic("今日は量子コンピュータの記事を読んだ"),"量子コンピュータ")
 def test_sqid(self):self.assertEqual(resolve_topic("SQUIDの話"),"超伝導量子干渉計")
 def test_explicit(self):self.assertEqual(resolve_topic("何かの記事","量子力学"),"量子力学")
 def test_no_topic(self):self.assertEqual(retry("読んだ")["status"],"TOPIC_UNRESOLVED")
 def test_success(self):
  with patch("wiki_retry_v0539.lookup",return_value=GOOD):
   r=retry("今日は量子コンピュータの記事を読んだ")
  self.assertEqual(r["status"],"EVIDENCE_FOUND")
  self.assertIn("量子力学の原理",r["answer"])
  self.assertEqual(r["source"],GOOD["url"])
 def test_no_promotion(self):
  with patch("wiki_retry_v0539.lookup",return_value=GOOD):r=retry("量子コンピュータ")
  self.assertFalse(r["verified"]);self.assertFalse(r["train_ready"]);self.assertFalse(r["promoted"])
 def test_not_found(self):
  with patch("wiki_retry_v0539.lookup",return_value={"status":"NOT_FOUND"}):r=retry("量子コンピュータ")
  self.assertEqual(r["status"],"EVIDENCE_UNAVAILABLE")
 def test_short_evidence(self):
  with patch("wiki_retry_v0539.lookup",return_value={**GOOD,"extract":"短い。"}):r=retry("量子コンピュータ")
  self.assertEqual(r["status"],"EVIDENCE_INSUFFICIENT")
 def test_chat_integration(self):
  s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(s)
  self.assertIn('user_text=="/wiki"',s)
  self.assertIn('user_text=="/wiki status"',s)
if __name__=="__main__":unittest.main()
