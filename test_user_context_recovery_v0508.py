import ast
import unittest
from pathlib import Path
from user_context_recovery_v0508 import UserContext

class UserContextRecoveryTests(unittest.TestCase):
 def test_initial(self):
  c=UserContext();self.assertIsNone(c.recovery("こんにちは"))
 def test_movie(self):
  c=UserContext();c.observe("今日は映画について話そう")
  self.assertIn("映画",c.recovery("今日は映画について話そう"))
 def test_avengers(self):
  c=UserContext();c.observe("アベンジャーズが好きです")
  self.assertIn("アベンジャーズ",c.recovery("アベンジャーズが好きです"))
 def test_continuation(self):
  c=UserContext();c.observe("映画ではアベンジャーズが好きです")
  self.assertIn("登場人物",c.recovery("続きの話を"))
 def test_preserve_subject_on_continuation(self):
  c=UserContext();c.observe("アベンジャーズが好き")
  c.observe("続きの話を")
  self.assertEqual(c.subject,"アベンジャーズ")
 def test_switch_topic(self):
  c=UserContext();c.observe("アベンジャーズが好き")
  c.observe("音楽の話をしよう")
  self.assertEqual(c.topic,"音楽")
  self.assertIsNone(c.subject)
 def test_music(self):
  c=UserContext();c.observe("音楽の話をしよう")
  self.assertIn("アーティスト",c.recovery("続きの話を"))
 def test_unknown_no_fallback(self):
  c=UserContext();c.observe("こんばんは")
  self.assertIsNone(c.recovery("話そう"))
 def test_reset_new_state(self):
  c=UserContext();c.observe("映画について")
  c=UserContext()
  self.assertIsNone(c.topic)
 def test_runtime_syntax(self):
  t=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(t)
  self.assertIn("cha_user_context.observe(raw_user_text)",t)
  self.assertIn("recovery=USER_CONTEXT_TEMPLATE",t)
 def test_runtime_does_not_trust_fallback(self):
  t=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  self.assertIn("if accepted:",t)
  self.assertIn("history.append((user_text, reply))",t)
  self.assertIn("recovery_reply = None",t)
 def test_legacy_sleep(self):
  t=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  self.assertIn('if command == "/sleep":',t)
if __name__=="__main__":unittest.main()
