import ast
import unittest
from pathlib import Path
from unknown_term_detection_v0516 import detect,probe

class UnknownTermDetectionTests(unittest.TestCase):
 def test_squid(self):
  self.assertIn("SQUID",detect("昨日SQUIDを使った量子センサーの記事を読んだよ"))
 def test_known(self):
  self.assertNotIn("GPU",detect("GPUについて話そう"))
 def test_known_topic(self):
  self.assertEqual(detect("映画について話そう"),[])
 def test_quoted(self):
  self.assertIn("新しい機器",detect("「新しい機器」を見た"))
 def test_duplicate(self):
  self.assertEqual(detect("SQUIDとSQUID"),["SQUID"])
 def test_lowercase_excluded(self):
  self.assertEqual(detect("hello world"),[])
 def test_custom_known(self):
  self.assertEqual(detect("SQUID",known={"SQUID"}),[])
 def test_diagnostic(self):
  d=probe("SQUIDって何")
  self.assertTrue(d["lookup_required"])
  self.assertFalse(d["retrieved"])
 def test_no_auto_learning(self):
  self.assertFalse(probe("SQUID")["train_ready"])
 def test_limit(self):
  self.assertEqual(len(detect("SQUID ABCD MNOP",limit=1)),1)
 def test_limit_invalid(self):
  with self.assertRaises(ValueError):detect("SQUID",limit=0)
 def test_chat_syntax(self):
  s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(s)
  self.assertIn("cha_unknown_term_probe(raw_user_text)",s)
 def test_no_legacy_sleep_change(self):
  s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  self.assertIn('if command == "/sleep":',s)
if __name__=="__main__":unittest.main()
