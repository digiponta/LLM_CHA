import unittest
from conversation_semantic_memory_v042857 import new_memory
from incremental_semantic_memory_v042859 import append
from semantic_context_reconstruction_v042860 import retrieve,reconstruct

class ContextReconstructionTests(unittest.TestCase):
 def state(self):
  s=new_memory("session")
  append(s,"user","私は車を持っていない")
  append(s,"assistant","そうなんですね")
  return s
 def test_retrieval(self):
  self.assertEqual(len(retrieve(self.state(),"車はありますか")),1)
 def test_avoid_irrelevant(self):
  self.assertEqual(retrieve(self.state(),"映画の話"),[])
 def test_unverified(self):
  self.assertIn("未検証",reconstruct(self.state(),"車について")["context"])
 def test_provenance(self):
  self.assertEqual(retrieve(self.state(),"車の話")[0]["source_turns"],[1])
 def test_ready(self):
  self.assertEqual(reconstruct(self.state(),"車は？")["status"],"ready")
 def test_budget_fails_closed(self):
  r=reconstruct(self.state(),"車は？",max_chars=10)
  self.assertEqual(r["status"],"budget_exceeded")
  self.assertIsNone(r["context"])
 def test_no_recent(self):
  self.assertEqual(reconstruct(self.state(),"車は？",recent_turns=0)["recent_turn_count"],0)
 def test_conflict_group_retained(self):
  s=self.state()
  append(s,"user","私は車を持っています")
  r=retrieve(s,"車",top_k=1)
  self.assertEqual(len(r),2)
  self.assertTrue(all(p["conflict_unresolved"] for p in r))
 def test_no_prompt_without_query(self):
  with self.assertRaises(ValueError):retrieve(self.state()," ")
 def test_no_training(self):
  self.assertFalse(reconstruct(self.state(),"車は？")["train_ready"])
if __name__=="__main__":unittest.main()
