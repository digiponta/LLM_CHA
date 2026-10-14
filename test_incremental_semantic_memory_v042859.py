import tempfile
import unittest
from pathlib import Path
from conversation_semantic_memory_v042857 import new_memory
from incremental_semantic_memory_v042859 import append,save_atomic,load

class IncrementalTests(unittest.TestCase):
 def test_increment(self):
  m=new_memory("s");append(m,"user","私は車を持っていない")
  self.assertEqual(m["last_turn"],1)
 def test_duplicate_consolidated(self):
  m=new_memory("s")
  append(m,"user","私は車を持っていない")
  append(m,"user","私は車を持っていません")
  self.assertEqual(len(m["proposition_index"]),1)
  self.assertEqual(m["proposition_index"][0]["source_turns"],[1,2])
 def test_polarity_conflict(self):
  m=new_memory("s")
  append(m,"user","私は車を持っていない")
  append(m,"user","私は車を持っています")
  self.assertEqual(len(m["conflict_candidates"]),1)
  self.assertFalse(m["conflict_candidates"][0]["resolved"])
 def test_evidence_preservation(self):
  m=new_memory("s")
  append(m,"user","私は車を持っていない")
  append(m,"user","私は車を持っています")
  self.assertEqual(len(m["propositions"]),2)
 def test_topic_history(self):
  m=new_memory("s")
  append(m,"user","映画が好きです")
  append(m,"user","車のことを話そう")
  self.assertEqual(len(m["topic_transitions"]),2)
 def test_no_transition_same_topic(self):
  m=new_memory("s")
  append(m,"user","映画について")
  append(m,"user","映画を見ます")
  self.assertEqual(len(m["topic_transitions"]),1)
 def test_atomic_round_trip(self):
  m=new_memory("s");append(m,"user","私は車を持っていない")
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"state.json"
   save_atomic(m,p)
   saved=load(p)
   self.assertEqual(saved["proposition_index"],m["proposition_index"])
 def test_continue_after_load(self):
  m=new_memory("s");append(m,"user","私は車を持っていない")
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"state.json";save_atomic(m,p);m2=load(p)
   append(m2,"user","私は車を持っています")
   self.assertEqual(m2["last_turn"],2)
   self.assertEqual(len(m2["conflict_candidates"]),1)
 def test_reject_unsafe(self):
  m=new_memory("s");m["train_ready"]=True
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):save_atomic(m,Path(d)/"memory.json")
 def test_rollback(self):
  m=new_memory("s")
  with self.assertRaises(ValueError):append(m,"system","映画")
  self.assertEqual(m["last_turn"],0)
if __name__=="__main__":unittest.main()
