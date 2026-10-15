import ast
import unittest
from pathlib import Path
from persona_context_v0550 import PersonaContext
class ContextTests(unittest.TestCase):
 def test_two_turns(self):
  p=PersonaContext()
  a=p.handle("今日は、量子コンピュータの記事を読んだ")
  b=p.handle("量子ビットについて書かれていた")
  self.assertEqual(a["intent"],"ARTICLE_SHARING")
  self.assertEqual(b["intent"],"ARTICLE_DETAIL_SHARING")
  self.assertIn("量子ビット",b["answer"])
 def test_neutral(self):
  p=PersonaContext("neutral")
  p.handle("今日は、量子コンピュータの記事を読んだ")
  self.assertIn("ましたか？",p.handle("量子ビットについて書かれていた")["answer"])
 def test_only_one(self):
  p=PersonaContext();p.handle("今日は、量子コンピュータの記事を読んだ")
  p.handle("量子ビットについて書かれていた")
  self.assertIsNone(p.handle("別の話が書かれていた"))
 def test_question_bypasses(self):
  p=PersonaContext();p.handle("今日は、量子コンピュータの記事を読んだ")
  self.assertIsNone(p.handle("量子ビットとは？"))
  self.assertIsNone(p.handle("量子ビットについて書かれていた"))
 def test_new_topic(self):
  p=PersonaContext();p.handle("今日は、量子コンピュータの記事を読んだ")
  p.handle("今日は、天文学の記事を読んだ")
  self.assertIn("天文学",p.handle("星について書かれていた")["answer"])
 def test_topic_switch(self):
  p=PersonaContext();p.handle("今日は、量子コンピュータの記事を読んだ")
  p.handle("今日は散歩した")
  self.assertIsNone(p.handle("量子ビットについて書かれていた"))
 def test_no_learning(self):
  p=PersonaContext();p.handle("今日は、量子コンピュータの記事を読んだ")
  r=p.handle("量子ビットについて書かれていた")
  self.assertFalse(r["train_ready"]);self.assertFalse(r["auto_lookup"]);self.assertFalse(r["auto_promote"])
 def test_reset(self):
  p=PersonaContext();p.handle("今日は、量子コンピュータの記事を読んだ");p.clear()
  self.assertIsNone(p.handle("量子ビットについて書かれていた"))
 def test_chat(self):
  s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(s);self.assertIn("cha_persona_context.handle(raw_user_text)",s)
if __name__=="__main__":unittest.main()
