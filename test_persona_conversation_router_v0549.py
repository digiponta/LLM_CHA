import ast
import unittest
from pathlib import Path
from persona_conversation_router_v0549 import classify,respond
class PersonaConversationTests(unittest.TestCase):
 def test_article(self):
  r=respond("今日は、量子コンピュータの記事を読んだ")
  self.assertIsNotNone(r);self.assertIn("量子コンピュータの記事",r["answer"])
 def test_neutral(self):
  a=respond("今日は、量子コンピュータの記事を読んだ")
  b=respond("今日は、量子コンピュータの記事を読んだ","neutral")
  self.assertNotEqual(a["answer"],b["answer"])
 def test_unknown_topic_fine(self):
  r=respond("今日は、未知概念の記事を読んだ")
  self.assertFalse(r["knowledge_asserted"])
 def test_question_not_routed(self):
  for q in ("量子コンピュータとは？","量子コンピュータについて教えて","今日は何を読んだ？"):
   self.assertIsNone(respond(q))
 def test_command_not_routed(self):self.assertIsNone(respond("/wiki"))
 def test_daily(self):self.assertEqual(classify("今日は散歩した")["intent"],"DAILY_SHARING")
 def test_ambiguous_not_routed(self):self.assertIsNone(respond("量子コンピュータは万能だ"))
 def test_no_auto(self):
  r=respond("今日は、量子コンピュータの記事を読んだ")
  self.assertFalse(r["auto_lookup"]);self.assertFalse(r["auto_promote"]);self.assertFalse(r["train_ready"])
 def test_chat(self):
  s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(s)
  # v0.5.50 routes through PersonaContext, which delegates sharing to v0.5.49.
  from persona_context_v0550 import PersonaContext
  self.assertEqual(PersonaContext().handle("今日は散歩した")["route"],"PERSONA_CONVERSATION_SHARING")
  call="cha_persona_context.handle(raw_user_text)"
  self.assertIn(call,s)
  self.assertLess(s.index(call),s.index("wiki_followup=cha_wiki_conversation.respond(raw_user_text)"))
if __name__=="__main__":unittest.main()
