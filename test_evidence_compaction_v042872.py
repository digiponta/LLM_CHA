import json
import unittest
from benchmark_long_conversation_resources_v042871 import make_session
from benchmark_evidence_compaction_v042872 import project,compare,benchmark,serialized_size

class EvidenceCompactionTests(unittest.TestCase):
 def test_three_modes(self):
  x=compare(10)["variants"]
  self.assertEqual(set(x),{"full","minimal","semantic_only"})
 def test_size(self):
  x=compare(10)["variants"]
  self.assertEqual(x["minimal"]["bytes_vs_full"],x["minimal"]["bytes"]-x["full"]["bytes"])
  self.assertEqual(x["minimal"]["smaller_than_full"],x["minimal"]["bytes"]<x["full"]["bytes"])
  self.assertGreater(x["minimal"]["bytes"],x["full"]["bytes"])  # synthetic short utterances
 def test_semantic_no_original(self):
  d=project(make_session(10),"semantic_only")
  self.assertNotIn("original_utterance",json.dumps(d))
  self.assertNotIn("私は音楽が好き",json.dumps(d,ensure_ascii=False))
 def test_minimal_span(self):
  d=project(make_session(2),"minimal")
  self.assertTrue(d["records"][0]["evidence_span"])
 def test_full_evidence(self):
  d=project(make_session(2),"full")
  self.assertEqual(d["records"][0]["original_utterance"],"私は音楽が好き")
 def test_uncovered(self):
  d=project(make_session(10,3),"semantic_only")
  self.assertEqual(d["uncovered_turn_ids"],[3,6,9])
 def test_no_eviction(self):
  x=compare(10)
  self.assertFalse(x["deletion_performed"])
  self.assertTrue(all(not v["approved_for_eviction"] for v in x["variants"].values()))
 def test_non_fact(self):
  d=project(make_session(3),"full")
  self.assertEqual(d["truth_state"],"UNVERIFIED")
  self.assertFalse(d["fact_promoted"])
 def test_repeated_count(self):
  d=project(make_session(10),"semantic_only")
  self.assertEqual(len(d["records"]),10)
 def test_invalid_mode(self):
  with self.assertRaises(ValueError):project(make_session(2),"bad")
 def test_benchmark_rows(self):
  b=benchmark((10,20),unmatched_every=5)
  self.assertEqual(len(b["rows"]),2)
  self.assertTrue(b["dry_run_only"])
 def test_bytes_utf8(self):
  d=project(make_session(2),"minimal")
  self.assertEqual(serialized_size(d),len((json.dumps(d,ensure_ascii=False,indent=2)+"\n").encode("utf-8")))
if __name__=="__main__":unittest.main()
