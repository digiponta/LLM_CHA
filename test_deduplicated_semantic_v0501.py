import unittest
from copy import deepcopy
from benchmark_long_conversation_resources_v042871 import make_session
from benchmark_deduplicated_semantic_v0501 import build,verify,compare,benchmark

class DeduplicatedSemanticTests(unittest.TestCase):
 def test_merge(self):
  p=build(make_session(100))
  self.assertLess(len(p["propositions"]),100)
 def test_all_occurrences(self):
  p=build(make_session(100))
  self.assertEqual(sum(len(x["occurrences"]) for x in p["propositions"]),100)
 def test_verify(self):
  m=make_session(20)
  self.assertTrue(verify(m,build(m)))
 def test_uncovered(self):
  m=make_session(10,3)
  p=build(m)
  self.assertEqual(p["uncovered_turn_ids"],[3,6,9])
  self.assertTrue(verify(m,p))
 def test_mutated_occurrence(self):
  m=make_session(10);p=build(m)
  p["propositions"][0]["occurrences"][0][0]=999
  with self.assertRaises(ValueError):verify(m,p)
 def test_changed_source(self):
  m=make_session(10);p=build(m)
  m2=make_session(10,3)
  with self.assertRaises(ValueError):verify(m2,p)
 def test_speaker_scoped(self):
  p=build(make_session(100))
  self.assertTrue(all(x["speaker"] in ("A","B") for x in p["propositions"]))
 def test_safe(self):
  p=build(make_session(10))
  self.assertFalse(p["approved_for_eviction"])
  self.assertFalse(p["fact_promoted"])
 def test_sizes(self):
  c=compare(100)
  self.assertEqual(c["bytes_saved"],c["raw_candidate_bytes"]-c["deduplicated_bytes"])
 def test_report(self):
  r=benchmark((10,20),unmatched_every=5)
  self.assertTrue(r["dry_run_only"])
  self.assertEqual(len(r["rows"]),2)
 def test_invalid(self):
  with self.assertRaises(ValueError):benchmark((0,))
  with self.assertRaises(ValueError):benchmark((10,),-1)
if __name__=="__main__":unittest.main()
