import ast
import json
import tempfile
import unittest
from pathlib import Path
from interactive_unknown_learning_v0510 import UnknownTeaching,concept_from,classify

class InteractiveUnknownTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.addCleanup(self.tmp.cleanup)
  self.path=Path(self.tmp.name)/"candidates.json"
  self.t=UnknownTeaching(self.path)
 def test_concept(self):
  self.assertEqual(concept_from("量子センサーとは何ですか"),"量子センサー")
 def test_definition_intent(self):
  self.assertEqual(concept_from("量子センサーについて教えて"),"量子センサー")
 def test_movie_not_teach(self):
  self.assertIsNone(self.t.begin("映画について話そう","topic grounding absent: 映画"))
 def test_begin(self):
  self.assertIn("教えて",self.t.begin("量子センサーとは何ですか","low response agreement"))
 def test_confirm_store(self):
  self.t.begin("量子センサーとは何ですか","unknown")
  self.assertIn("保存してよい",self.t.handle("量子状態を用いるセンサーです。"))
  self.assertIn("未検証",self.t.handle("はい"))
  row=json.loads(self.path.read_text(encoding="utf-8"))[0]
  self.assertEqual(row["truth_state"],"USER_REPORTED_UNVERIFIED")
  self.assertFalse(row["train_ready"])
  self.assertFalse(row["approved_for_sleep"])
 def test_no_cancellation(self):
  self.t.begin("量子センサーとは何ですか","unknown")
  self.t.handle("説明");self.t.handle("いいえ")
  self.assertFalse(self.path.exists())
 def test_no_auto_confirmation(self):
  self.t.begin("量子センサーとは何ですか","unknown")
  self.t.handle("説明")
  self.assertIn("はい",self.t.handle("あとで"))
  self.assertFalse(self.path.exists())
 def test_lookup(self):
  self.t.begin("量子センサーとは何ですか","unknown")
  self.t.handle("量子のセンサー");self.t.handle("はい")
  self.assertEqual(len(self.t.lookup("量子センサー")),1)
  self.assertEqual(len(self.t.lookup("別の概念")),0)
 def test_idempotent_confirmation(self):
  for _ in range(2):
   self.t.begin("量子センサーとは何ですか","unknown")
   self.t.handle("量子のセンサー");self.t.handle("はい")
  self.assertEqual(len(self.t.lookup("量子センサー")),1)
 def test_reject_command_as_explanation(self):
  self.t.begin("量子センサーとは何ですか","unknown")
  self.assertIn("文章",self.t.handle("/train"))
 def test_syntax(self):
  s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(s)
  self.assertIn("cha_unknown_teacher.begin(",s)
  self.assertIn('if user_text.startswith("/cha-unknown ")',s)
 def test_legacy_sleep(self):
  s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  self.assertIn('if command == "/sleep":',s)
if __name__=="__main__":unittest.main()
