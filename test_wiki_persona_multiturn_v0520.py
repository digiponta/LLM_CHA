import ast
import unittest
from pathlib import Path
from wiki_persona_multiturn_v0520 import WikiConversation

WIKI={"status":"FOUND","title":"超伝導量子干渉計",
"url":"https://ja.wikipedia.org/wiki/超伝導量子干渉計",
"extract":"SQUIDは非常に感度の高い磁気センサの一種である。ジョセフソン接合を利用した超伝導回路によって微弱な磁場を測定する。医療や物理計測の研究に利用される。"}
class PersonaMultiTurnTests(unittest.TestCase):
 def test_more(self):
  c=WikiConversation();c.offer(WIKI)
  r=c.respond("もう少し詳しく")
  self.assertIn("ジョセフソン接合",r["answer"])
  self.assertEqual(r["route"],"PERSONA_WIKIPEDIA_CONTEXT_FOLLOWUP")
 def test_usage(self):
  c=WikiConversation();c.offer(WIKI)
  r=c.respond("何に使われるの？")
  self.assertIn("医療",r["answer"])
 def test_why(self):
  c=WikiConversation();c.offer(WIKI)
  self.assertIn("ジョセフソン",c.respond("なぜ高感度なの？")["answer"])
 def test_no_repeated_evidence(self):
  c=WikiConversation();c.offer(WIKI)
  c.respond("もう少し詳しく")
  self.assertNotIn("ジョセフソン",c.respond("もう少し詳しく")["answer"])
 def test_source(self):
  c=WikiConversation();c.offer(WIKI)
  self.assertEqual(c.respond("もう少し詳しく")["source"],WIKI["url"])
 def test_unverified(self):
  c=WikiConversation();c.offer(WIKI)
  r=c.respond("もう少し詳しく")
  self.assertFalse(r["verified"])
  self.assertFalse(r["train_ready"])
 def test_no_evidence(self):
  c=WikiConversation();c.offer(WIKI)
  r=c.respond("なぜ宇宙が生まれたの？")
  self.assertIn(r["route"],("PERSONA_WIKIPEDIA_CONTEXT_FOLLOWUP","WIKIPEDIA_EVIDENCE_INSUFFICIENT"))
 def test_unrelated_clears(self):
  c=WikiConversation();c.offer(WIKI)
  self.assertIsNone(c.respond("今日はいい天気"))
  self.assertIsNone(c.respond("もう少し詳しく"))
 def test_neutral(self):
  c=WikiConversation(persona="neutral");c.offer(WIKI)
  self.assertIn("記載されています",c.respond("もう少し詳しく")["answer"])
 def test_failed_lookup(self):
  c=WikiConversation();c.offer({"status":"LOOKUP_FAILED"})
  self.assertIsNone(c.respond("もう少し詳しく"))
 def test_chat_parse(self):
  source=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(source)
  self.assertIn("from wiki_persona_multiturn_v0520 import WikiConversation",source)
 def test_sleep_preserved(self):
  source=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  self.assertIn('if command == "/sleep":',source)
if __name__=="__main__":unittest.main()
