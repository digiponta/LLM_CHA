import ast
import tempfile
import unittest
from pathlib import Path
from chat_conversation_bridge_v0506 import ConversationBridge

class ChatConversationBridgeTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory()
  self.addCleanup(self.t.cleanup)
  self.bridge=ConversationBridge(Path(self.t.name)/"conversation_memory_local")
 def test_opt_in(self):
  self.assertFalse(self.bridge.record_accepted("hello","world"))
  self.assertFalse(self.bridge.status()["enabled"])
 def test_record_and_close(self):
  self.bridge.start("sample")
  self.assertTrue(self.bridge.record_accepted("私は映画が好き","こんにちは"))
  self.assertEqual(self.bridge.status()["turns"],2)
  self.assertFalse(self.bridge.close()["active"])
 def test_reopen_rejected(self):
  self.bridge.start("sample");self.bridge.close()
  with self.assertRaises(ValueError):self.bridge.start("sample")
 def test_invalid_id(self):
  with self.assertRaises(ValueError):self.bridge.start("../escape")
 def test_sleep_is_not_training(self):
  self.bridge.start("sample")
  self.bridge.record_accepted("私は映画が好き","はい")
  self.bridge.close()
  result=self.bridge.sleep()
  self.assertEqual(result["processed_turn"],2)
  self.assertEqual(self.bridge.sleep()["new_turns"],0)
 def test_migration_keeps_source(self):
  self.bridge.start("sample")
  self.bridge.record_accepted("私は映画が好き","こんにちは")
  self.bridge.close()
  result=self.bridge.migrate()
  self.assertTrue(result["source_retained"])
  self.assertTrue(self.bridge.source.exists())
 def test_active_migration_rejected(self):
  self.bridge.start("sample")
  with self.assertRaises(ValueError):self.bridge.migrate()
 def test_active_sleep_rejected(self):
  self.bridge.start("sample")
  with self.assertRaises(ValueError):self.bridge.sleep()
 def test_same_id_while_active(self):
  self.bridge.start("sample")
  with self.assertRaises(ValueError):self.bridge.start("other")
 def test_chat_syntax(self):
  text=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(text)
  self.assertIn('if command in ("/cha-start"',text)
  self.assertIn('cha_bridge.record_accepted(raw_user_text, reply)',text)
 def test_old_sleep_preserved(self):
  text=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  self.assertIn('if command == "/sleep":',text)
  self.assertIn('prepare_semantic_sleep_pairs(',text)
if __name__=="__main__":unittest.main()
