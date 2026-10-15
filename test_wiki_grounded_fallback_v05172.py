import ast
import unittest
from pathlib import Path
from wiki_grounded_fallback_v05172 import grounded_reply

EXAMPLE={"status":"FOUND","title":"超伝導量子干渉計",
"url":"https://ja.wikipedia.org/wiki/%E8%B6%85%E4%BC%9D%E5%B0%8E%E9%87%8F%E5%AD%90%E5%B9%B2%E6%B8%89%E8%A8%88",
"extract":"超伝導量子干渉計 (SQUID) とは、ジョセフソン接合を含む環状超伝導体を用いる高感度の磁気センサである。"}
class WikiGroundedTests(unittest.TestCase):
 def test_relevant(self):
  r=grounded_reply(EXAMPLE,"昨日SQUIDを使った量子センサーの記事を読んだよ")
  self.assertIn("ジョセフソン",r["answer"])
  self.assertIn("その記事では",r["answer"])
 def test_provenance(self):
  r=grounded_reply(EXAMPLE,"SQUID")
  self.assertEqual(r["source"],EXAMPLE["url"])
 def test_unverified(self):
  self.assertFalse(grounded_reply(EXAMPLE,"SQUID")["verified"])
 def test_no_training(self):
  self.assertFalse(grounded_reply(EXAMPLE,"SQUID")["train_ready"])
 def test_unavailable(self):
  self.assertIsNone(grounded_reply({"status":"LOOKUP_FAILED"},"SQUID"))
 def test_no_empty(self):
  self.assertIsNone(grounded_reply({**EXAMPLE,"extract":""},"SQUID"))
 def test_bad_source(self):
  self.assertIsNone(grounded_reply({**EXAMPLE,"url":"https://example.org"},"SQUID"))
 def test_syntax_and_route(self):
  src=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(src)
  self.assertIn("raw_generation=SKIPPED",src)
 def test_sleep_preserved(self):
  src=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  self.assertIn('if command == "/sleep":',src)
if __name__=="__main__":unittest.main()
