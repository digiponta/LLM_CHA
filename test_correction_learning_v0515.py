import ast
import json
import tempfile
import unittest
from pathlib import Path
from correction_learning_v0515 import CorrectionSession
from interactive_unknown_learning_v0510 import UnknownTeaching
from usage_confidence_v0513 import update

class CorrectionTests(unittest.TestCase):
 def setUp(self):
  tmp=tempfile.TemporaryDirectory()
  self.addCleanup(tmp.cleanup)
  self.path=Path(tmp.name)/"candidates.json"
  t=UnknownTeaching(self.path)
  t.begin("量子センサーとは何ですか？","unknown")
  t.handle("古い説明")
  t.handle("はい")
  update(self.path,1,"negative")
  self.c=CorrectionSession()
 def test_start(self):
  self.assertIn("教えて",self.c.start(self.path,1))
 def test_confirm(self):
  self.c.start(self.path,1)
  self.assertIn("はい／いいえ",self.c.respond(self.path,"新しい説明"))
 def test_save(self):
  self.c.start(self.path,1)
  self.c.respond(self.path,"修正内容")
  self.assertIn("ID 2",self.c.respond(self.path,"はい"))
  rows=json.loads(self.path.read_text(encoding="utf-8"))
  self.assertEqual(rows[1]["corrects_candidate_id"],1)
  self.assertEqual(rows[0]["operational_status"],"CONTESTED")
 def test_never_train(self):
  self.c.start(self.path,1)
  self.c.respond(self.path,"修正内容")
  self.c.respond(self.path,"はい")
  row=json.loads(self.path.read_text(encoding="utf-8"))[1]
  self.assertFalse(row["verified"])
  self.assertFalse(row["train_ready"])
  self.assertFalse(row["approved_for_sleep"])
 def test_cancel(self):
  self.c.start(self.path,1)
  self.c.respond(self.path,"修正内容")
  self.c.respond(self.path,"いいえ")
  self.assertEqual(len(json.loads(self.path.read_text(encoding="utf-8"))),1)
 def test_cancel_explanation(self):
  self.c.start(self.path,1)
  self.c.respond(self.path,"/cancel")
  self.assertIsNone(self.c.pending)
 def test_reject_command(self):
  self.c.start(self.path,1)
  self.assertIn("文章",self.c.respond(self.path,"/train"))
 def test_confirmation_requires_yes(self):
  self.c.start(self.path,1)
  self.c.respond(self.path,"訂正")
  self.assertIn("はい",self.c.respond(self.path,"正しいです"))
 def test_no_prior(self):
  self.assertIsNone(self.c.respond(self.path,"はい"))
 def test_state_after_save(self):
  self.c.start(self.path,1)
  self.c.respond(self.path,"訂正")
  self.c.respond(self.path,"はい")
  self.assertIsNone(self.c.pending)
 def test_runtime_syntax(self):
  src=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(src)
  self.assertIn("cha_correction_session.respond(",src)
  self.assertIn("cha_correction_session.start(",src)
 def test_legacy_sleep(self):
  src=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  self.assertIn('if command == "/sleep":',src)
if __name__=="__main__":unittest.main()
