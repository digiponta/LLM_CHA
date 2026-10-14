import json
import tempfile
import unittest
from pathlib import Path
from conversation_resource_memory_v042866 import (
 new_conversation,append_turn,close_session,sleep_checkpoint,
 can_evict,evict_to_budget,size_bytes,write_json_atomic,validate
)
class ConversationResourceTests(unittest.TestCase):
 def record(self,cid,done=False,active=False):
  m=new_conversation(cid)
  append_turn(m,"A","私は音楽が好きです")
  close_session(m)
  if done:sleep_checkpoint(m,1,completed=True)
  if active:m["active"]=True
  return m
 def test_category(self):
  m=new_conversation("c");self.assertEqual(m["category"],"CONVERSATION")
 def test_append(self):
  m=new_conversation("c");append_turn(m,"B","こんにちは")
  self.assertEqual((m["last_turn"],m["turns"][0]["speaker"]),(1,"B"))
 def test_pending_protected(self):
  self.assertFalse(can_evict(self.record("c")))
 def test_completed_evictable(self):
  self.assertTrue(can_evict(self.record("c",done=True)))
 def test_active_protected(self):
  self.assertFalse(can_evict(self.record("c",done=True,active=True)))
 def test_default_no_loss(self):
  m=self.record("c")
  stay,audit=evict_to_budget([m],0)
  self.assertEqual(len(stay),1);self.assertFalse(audit["budget_satisfied"])
 def test_explicit_loss(self):
  m=self.record("c")
  stay,audit=evict_to_budget([m],0,allow_unprocessed_loss=True)
  self.assertEqual(stay,[]);self.assertTrue(audit["removed"][0]["had_unprocessed_turns"])
 def test_checkpoint(self):
  m=self.record("c");sleep_checkpoint(m,1,completed=True)
  self.assertEqual(m["status"],"SLEEP_COMPLETED")
 def test_no_partial_completion(self):
  m=self.record("c")
  with self.assertRaises(ValueError):sleep_checkpoint(m,0,completed=True)
 def test_processed_first(self):
  a=self.record("a");b=self.record("b",done=True)
  stay,audit=evict_to_budget([a,b],size_bytes(a))
  self.assertEqual([x["conversation_id"] for x in stay],["a"])
 def test_atomic(self):
  m=self.record("c")
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"c.json";write_json_atomic(m,p)
   self.assertEqual(json.loads(p.read_text(encoding="utf-8"))["category"],"CONVERSATION")
 def test_rollback_bad_turn(self):
  m=new_conversation("c")
  with self.assertRaises(ValueError):append_turn(m,"B","Hi",turn_id=2)
  self.assertEqual(m["last_turn"],0)
 def test_duplicate_ids(self):
  m=self.record("c")
  with self.assertRaises(ValueError):evict_to_budget([m,m],0)
 def test_no_training(self):
  self.assertFalse(validate(self.record("c"))["train_ready"])
if __name__=="__main__":unittest.main()
