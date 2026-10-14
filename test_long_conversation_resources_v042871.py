import unittest
from benchmark_long_conversation_resources_v042871 import (
 make_session,one_benchmark,benchmark)

class LongConversationResourceTests(unittest.TestCase):
 def test_100_turns(self):
  r=one_benchmark(100)
  self.assertEqual(r["turns"],100)
  self.assertEqual(r["candidate_count"],100)
 def test_500_turns(self):
  r=one_benchmark(500)
  self.assertEqual(r["candidate_count"],500)
 def test_1000_turns(self):
  r=one_benchmark(1000)
  self.assertEqual(r["candidate_count"],1000)
 def test_covered(self):
  r=one_benchmark(10)
  self.assertEqual(r["uncovered_turns"],0)
  self.assertTrue(r["deletion_permitted"])
 def test_uncovered(self):
  r=one_benchmark(10,unmatched_every=3)
  self.assertGreater(r["uncovered_turns"],0)
  self.assertFalse(r["deletion_permitted"])
 def test_zero_eviction(self):
  r=one_benchmark(10,unmatched_every=2)
  self.assertEqual(r["potential_bytes_freed"],0)
 def test_dry_run(self):
  r=one_benchmark(10)
  self.assertFalse(r["deletion_performed"])
 def test_accounting(self):
  r=one_benchmark(10)
  self.assertEqual(r["bytes_before_eviction"],
      r["conversation_bytes"]+r["artifacts_total_bytes"])
  self.assertEqual(r["net_bytes_after_eviction"],
      r["bytes_before_eviction"]-r["potential_bytes_freed"])
 def test_conversation_identity(self):
  m=make_session(10)
  self.assertEqual(m["last_turn"],10)
  self.assertFalse(m["active"])
 def test_no_model_quality_claim(self):
  r=benchmark((10,20))
  self.assertIsNone(r["rows"][0]["model_response_quality"])
  self.assertTrue(r["dry_run_only"])
 def test_invalid(self):
  with self.assertRaises(ValueError):make_session(0)
  with self.assertRaises(ValueError):one_benchmark(3,unmatched_every=-1)
if __name__=="__main__":unittest.main()
