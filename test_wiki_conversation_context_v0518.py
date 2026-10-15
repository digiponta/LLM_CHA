import ast
import unittest
from pathlib import Path
from wiki_conversation_context_v0518 import WikiConversation

EXAMPLE={"status":"FOUND","title":"超伝導量子干渉計",
"url":"https://ja.wikipedia.org/wiki/%E8%B6%85%E4%BC%9D%E5%B0%8E%E9%87%8F%E5%AD%90%E5%B9%B2%E6%B8%89%E8%A8%88",
"extract":"SQUIDは超伝導を使う高感度磁気センサーである。ジョセフソン接合を利用して非常に弱い磁場を測定できる。"}
class WikiConversationTests(unittest.TestCase):
 def test_no_context(self):
  self.assertIsNone(WikiConversation().respond("もう少し詳しく"))
 def test_followup(self):
  c=WikiConversation();c.offer(EXAMPLE)
  r=c.respond("もう少し詳しく")
  self.assertIn("ジョセフソン",r["answer"])
  self.assertEqual(r["route"],"WIKIPEDIA_CONTEXT_FOLLOWUP")
 def test_provenance(self):
  c=WikiConversation();c.offer(EXAMPLE)
  self.assertEqual(c.respond("詳しく教えて")["source"],EXAMPLE["url"])
 def test_never_train(self):
  c=WikiConversation();c.offer(EXAMPLE)
  r=c.respond("その続き")
  self.assertFalse(r["verified"])
  self.assertFalse(r["train_ready"])
 def test_exhausted(self):
  c=WikiConversation();c.offer(EXAMPLE)
  c.respond("その続き")
  self.assertEqual(c.respond("その続き")["route"],"WIKIPEDIA_EVIDENCE_EXHAUSTED")
 def test_unrelated_clears(self):
  c=WikiConversation();c.offer(EXAMPLE)
  self.assertIsNone(c.respond("今日はいい天気"))
  self.assertIsNone(c.respond("その続き"))
 def test_fail_closed(self):
  c=WikiConversation();c.offer({"status":"LOOKUP_FAILED"})
  self.assertIsNone(c.respond("その続き"))
 def test_reset(self):
  c=WikiConversation();c.offer(EXAMPLE);c.clear()
  self.assertIsNone(c.respond("その続き"))
 def test_syntax_and_integration(self):
  src=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(src)
  self.assertIn("cha_wiki_conversation.offer(wiki_context)",src)
 def test_sleep_untouched(self):
  src=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  self.assertIn('if command == "/sleep":',src)
if __name__=="__main__":unittest.main()
