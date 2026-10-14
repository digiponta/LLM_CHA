import json
import tempfile
import unittest
from pathlib import Path
from conversation_resource_memory_v042866 import (
 new_conversation,append_turn,close_session,write_json_atomic)
from conversation_sleep_backend_v042868 import run,extract

class SleepBackendTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.addCleanup(self.tmp.cleanup)
  self.src=Path(self.tmp.name)/"sample.conversation.json"
  self.dst=Path(self.tmp.name)/"sample.candidates.json"
  self.m=new_conversation("synthetic-session")
  append_turn(self.m,"A","私は音楽が好き")
  append_turn(self.m,"B","映画が好き")
  close_session(self.m)
  write_json_atomic(self.m,self.src)
 def test_extract_candidate(self):
  a=extract(self.m)
  self.assertEqual(len(a["candidates"]),1)
  self.assertEqual(a["candidates"][0]["speaker"],"A")
 def test_sleep_completed(self):
  r=run(self.src,self.dst)
  self.assertEqual(r["status"],"SLEEP_COMPLETED")
  self.assertTrue(self.dst.exists())
 def test_unverified(self):
  run(self.src,self.dst)
  artifact=json.loads(self.dst.read_text(encoding="utf-8"))
  self.assertFalse(artifact["fact_promoted"])
  self.assertFalse(artifact["train_ready"])
 def test_replay(self):
  run(self.src,self.dst)
  again=run(self.src,self.dst)
  self.assertEqual(again["candidate_status"],"VERIFIED_EXISTING")
 def test_no_duplicate(self):
  run(self.src,self.dst)
  run(self.src,self.dst)
  self.assertEqual(len(json.loads(self.dst.read_text(encoding="utf-8"))["candidates"]),1)
 def test_failure_keeps_pending(self):
  self.dst.write_text('{"incorrect":true}',encoding="utf-8")
  with self.assertRaises(ValueError):run(self.src,self.dst)
  self.assertEqual(json.loads(self.src.read_text(encoding="utf-8"))["status"],"PENDING_SLEEP")
 def test_active_protected(self):
  m=new_conversation("active");append_turn(m,"A","私は音楽が好き")
  write_json_atomic(m,self.src)
  with self.assertRaises(ValueError):run(self.src,self.dst)
 def test_unsupported_identity(self):
  m=new_conversation("user-case");append_turn(m,"user","私は音楽が好き")
  close_session(m);write_json_atomic(m,self.src)
  with self.assertRaises(ValueError):run(self.src,self.dst)
 def test_source_change_rejected(self):
  run(self.src,self.dst)
  source=json.loads(self.src.read_text(encoding="utf-8"))
  from conversation_resource_memory_v042866 import append_turn
  append_turn(source,"A","私は京都に行った")
  write_json_atomic(source,self.src)
  with self.assertRaises(ValueError):run(self.src,self.dst)
 def test_nonfact(self):
  a=extract(self.m)
  self.assertEqual(a["category"],"PROPOSITION_CANDIDATES")
  self.assertEqual(a["truth_state"],"UNVERIFIED")
if __name__=="__main__":unittest.main()
