import ast
import json
import tempfile
import unittest
from pathlib import Path

from conversation_resource_memory_v042866 import new_conversation,append_turn,close_session,write_json_atomic
from chat_conversation_bridge_v0506 import ConversationBridge
from conversation_retrieval_v0509 import retrieve,restore_user_context

class ConversationRetrievalTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.root=Path(self.temp.name)/"memory"
  self.bridge=ConversationBridge(self.root)
  self.bridge.start("film")
  self.bridge.record_user("映画では、アベンジャーズが好きです")
  self.bridge.record_user("続きの話を")
  self.bridge.record_assistant("映画について話しましょう")
  self.bridge.record_user("音楽も好きです")
  self.bridge.close()

 def test_user_provenance(self):
  rows=self.bridge.recall("映画の話を")
  self.assertEqual(rows[0]["turn_id"],1)
  self.assertEqual(rows[0]["speaker"],"user")
 def test_no_ai_retrieval(self):
  rows=self.bridge.recall("映画について")
  self.assertTrue(all(r["speaker"]=="user" for r in rows))
  self.assertFalse(any("映画について話しましょう"==r["text"] for r in rows))
 def test_unverified(self):
  self.assertEqual(self.bridge.recall("映画")[0]["truth_state"],"USER_REPORTED_UNVERIFIED")
  self.assertFalse(self.bridge.recall("映画")[0]["trusted_fact"])
 def test_continuation(self):
  rows=self.bridge.recall("続きの話を")
  self.assertEqual(rows[0]["turn_id"],4)
  self.assertEqual(rows[0]["topic"],"音楽")
 def test_explicit_movie_continuation(self):
  rows=self.bridge.recall("映画の話の続きを")
  self.assertEqual(rows[0]["turn_id"],1)
  self.assertEqual(rows[0]["subject"],"アベンジャーズ")
 def test_cross_topic(self):
  rows=self.bridge.recall("音楽の話")
  self.assertEqual(len(rows),1)
  self.assertEqual(rows[0]["turn_id"],4)
 def test_restore(self):
  ctx,rows=restore_user_context(self.bridge.source,"続きを話そう")
  self.assertEqual(ctx.topic,"音楽")
  self.assertIsNone(ctx.subject)
  self.assertEqual(rows[0]["turn_id"],4)
 def test_restore_explicit_movie(self):
  ctx,rows=restore_user_context(self.bridge.source,"映画の話の続きを")
  self.assertEqual(ctx.subject,"アベンジャーズ")
  self.assertEqual(rows[0]["turn_id"],1)
 def test_reopen(self):
  other=ConversationBridge(self.root)
  other.load_closed("film")
  self.assertEqual(other.recall("映画")[0]["turn_id"],1)
 def test_limit(self):
  self.assertEqual(len(self.bridge.recall("続きの話を",1)),1)
 def test_invalid_limit(self):
  with self.assertRaises(ValueError):retrieve(self.bridge.source,"映画",0)
 def test_reject_bad_id(self):
  with self.assertRaises(ValueError):self.bridge.load_closed("../film")
 def test_cannot_load_active(self):
  active=ConversationBridge(self.root);active.start("active")
  with self.assertRaises(ValueError):self.bridge.load_closed("active")
 def test_runtime_syntax(self):
  s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(s)
  self.assertIn("cha_bridge.record_user(raw_user_text)",s)
  self.assertIn("cha_bridge.record_assistant(reply)",s)
  self.assertIn('"/cha-recall "',s)
 def test_no_legacy_sleep_change(self):
  s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  self.assertIn('if command == "/sleep":',s)
 def test_unrecognized_returns_empty(self):
  self.assertEqual(self.bridge.recall("量子力学とは"),[])
if __name__=="__main__":unittest.main()
