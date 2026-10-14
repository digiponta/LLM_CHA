import unittest
from conversation_semantic_memory_v042857 import new_memory,update,build_prompt_context

class MemoryTests(unittest.TestCase):
 def test_initial(self):
  s=new_memory("session");self.assertEqual(s["last_turn"],0);self.assertFalse(s["train_ready"])
 def test_keywords(self):
  s=new_memory("session");update(s,"user","東京では駐車場が高いので車を持っていない")
  self.assertIn("車",s["keywords"])
 def test_proposition_provenance(self):
  s=new_memory("session");update(s,"user","車を持っていない")
  p=s["propositions"][0]
  self.assertFalse(p["polarity"]);self.assertEqual(p["source_turn"],1)
  self.assertEqual(p["truth_state"],"USER_REPORTED_UNVERIFIED")
 def test_assistant_not_user_fact(self):
  s=new_memory("session");update(s,"assistant","車を持っていない")
  self.assertEqual(s["propositions"],[])
 def test_monotonic_turn(self):
  s=new_memory("session")
  with self.assertRaises(ValueError):update(s,"user","映画",turn_id=2)
 def test_rolling_context(self):
  s=new_memory("session")
  for i in range(8):update(s,"user",f"映画{i}",recent_limit=3)
  self.assertEqual(len(s["recent_turns"]),3)
  self.assertEqual(s["last_turn"],8)
 def test_prompt_is_non_authoritative(self):
  s=new_memory("session");update(s,"user","車を持っていない")
  self.assertFalse(build_prompt_context(s)["context_is_authoritative"])
 def test_no_invented_fact(self):
  s=new_memory("session");update(s,"user","車が好き")
  self.assertEqual(s["propositions"],[])
 def test_bad_role(self):
  s=new_memory("session")
  with self.assertRaises(ValueError):update(s,"system","東京")
 def test_no_training_promotion(self):
  s=new_memory("session");update(s,"user","車を持っていない")
  self.assertEqual(s["promotion_status"],"not_promoted")
  self.assertFalse(s["train_ready"])
if __name__=="__main__":unittest.main()
