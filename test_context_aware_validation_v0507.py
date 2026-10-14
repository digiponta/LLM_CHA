import ast
import unittest
from pathlib import Path
from context_aware_validation_v0507 import grounded,topic_for,resolve_context
class TopicGroundingTests(unittest.TestCase):
 def test_detect_movie(self):self.assertEqual(topic_for("アベンジャーズが好き"),"映画")
 def test_detect_music(self):self.assertEqual(topic_for("音楽の話"),"音楽")
 def test_no_topic(self):self.assertIsNone(topic_for("こんにちは"))
 def test_reject_hallucinated_movie(self):
  ok,reason=grounded("映画について話そう","テレビジョン・ホッホ、声を真で見て示した物理現象。")
  self.assertFalse(ok)
 def test_reject_avengers_off_topic(self):
  ok,_=grounded("映画では、アベンジャーズが好きです","宇宙は、人間が悪いのかは不適当な情報。")
  self.assertFalse(ok)
 def test_accept_on_topic(self):
  ok,_=grounded("映画について話そう","どんな映画が好きですか？")
  self.assertTrue(ok)
 def test_unknown_domain_not_blocked(self):
  ok,_=grounded("今日はいい天気","晴れですね")
  self.assertTrue(ok)
 def test_continuation(self):
  self.assertEqual(resolve_context("続きの話を","映画"),"映画の話の続きをしましょう。")
 def test_no_continuation(self):
  self.assertEqual(resolve_context("普通の会話","映画"),"普通の会話")
 def test_continuation_requires_topic(self):
  self.assertEqual(resolve_context("続きの話を",None),"続きの話を")
 def test_chat_syntax(self):
  s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(s)
  self.assertIn("cha_topic_grounded(",s)
  self.assertIn("cha_resolve_context(",s)
 def test_old_sleep_remains(self):
  s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  self.assertIn('if command == "/sleep":',s)
  self.assertIn('if command in ("/cha-start"',s)
if __name__=="__main__":unittest.main()
