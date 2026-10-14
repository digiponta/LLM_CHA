import ast
import tempfile
import unittest
from pathlib import Path
from interactive_unknown_learning_v0510 import UnknownTeaching
from usage_confidence_v0513 import summary,update

class UsageConfidenceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.addCleanup(self.tmp.cleanup)
  self.path=Path(self.tmp.name)/"candidates.json"
  t=UnknownTeaching(self.path)
  t.begin("量子センサーとは何ですか？","unknown")
  t.handle("量子状態を利用するセンサーです。")
  t.handle("はい")
 def test_initial(self):
  self.assertEqual(summary(self.path,1)["operational_status"],"PROVISIONAL")
 def test_use_no_approval(self):
  r=update(self.path,1,"used")
  self.assertEqual(r["usage_count"],1)
  self.assertEqual(r["usage_confidence"],0)
 def test_positive(self):
  self.assertGreater(update(self.path,1,"positive")["usage_confidence"],0)
 def test_promote_operational_not_verified(self):
  r=None
  for _ in range(5):r=update(self.path,1,"positive")
  self.assertEqual(r["operational_status"],"OPERATIONAL")
  self.assertFalse(r["verified"])
 def test_negative_contested(self):
  update(self.path,1,"positive")
  r=update(self.path,1,"negative")
  self.assertEqual(r["operational_status"],"CONTESTED")
 def test_negative_stays_contested(self):
  update(self.path,1,"negative")
  r=update(self.path,1,"positive")
  self.assertEqual(r["operational_status"],"CONTESTED")
 def test_never_trainable(self):
  r=update(self.path,1,"positive")
  self.assertFalse(r["train_ready"])
 def test_invalid_id(self):
  with self.assertRaises(ValueError):update(self.path,2,"positive")
 def test_invalid_action(self):
  with self.assertRaises(ValueError):update(self.path,1,"auto")
 def test_restart(self):
  update(self.path,1,"used")
  self.assertEqual(summary(self.path,1)["usage_count"],1)
 def test_runtime_syntax(self):
  s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(s)
  self.assertIn('"/cha-feedback "',s)
  self.assertIn('"/cha-usage "',s)
 def test_legacy_sleep(self):
  s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  self.assertIn('if command == "/sleep":',s)
if __name__=="__main__":unittest.main()
