import unittest
from copy import deepcopy
from benchmark_long_conversation_resources_v042871 import make_session
from benchmark_compact_evidence_v0502 import pack,verify,compare,benchmark

class CompactEvidenceTests(unittest.TestCase):
 def test_reconstruct_all(self):
  m=make_session(100)
  self.assertTrue(verify(m,pack(m)))
 def test_unmatched_preserved(self):
  m=make_session(10,3);p=pack(m)
  self.assertEqual(p["uncovered_turn_ids"],[3,6,9])
  self.assertIn("今日はいい天気ですね",p["texts"])
  self.assertTrue(verify(m,p))
 def test_dedup_text(self):
  p=pack(make_session(100))
  self.assertLess(len(p["texts"]),100)
 def test_dedup_proposition(self):
  p=pack(make_session(100))
  self.assertLess(len(p["propositions"]),100)
 def test_occurrences(self):
  p=pack(make_session(100))
  self.assertEqual(len(p["occurrences"]),100)
 def test_tampered_text(self):
  m=make_session(10);p=pack(m);p["texts"][0]="changed"
  with self.assertRaises(ValueError):verify(m,p)
 def test_tampered_turn(self):
  m=make_session(10);p=pack(m);p["turns"][0][1]="B"
  with self.assertRaises(ValueError):verify(m,p)
 def test_source_mismatch(self):
  m=make_session(10);p=pack(m)
  with self.assertRaises(ValueError):verify(make_session(10,3),p)
 def test_no_eviction(self):
  p=pack(make_session(10))
  self.assertFalse(p["approved_for_eviction"])
  self.assertFalse(p["fact_promoted"])
 def test_size_accounting(self):
  r=compare(100)
  self.assertEqual(r["bytes_saved_vs_conversation"],r["conversation_bytes"]-r["compact_evidence_bytes"])
 def test_1000(self):
  r=compare(1000)
  self.assertEqual(r["candidate_count"],1000)
  self.assertTrue(r["all_turns_reconstructed"])
 def test_report(self):
  r=benchmark((10,20),5)
  self.assertEqual(len(r["rows"]),2)
  self.assertTrue(r["dry_run_only"])
 def test_invalid(self):
  with self.assertRaises(ValueError):benchmark((0,))
  with self.assertRaises(ValueError):benchmark((10,),-1)
if __name__=="__main__":unittest.main()
