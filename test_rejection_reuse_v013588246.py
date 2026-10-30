import tempfile
import unittest
from pathlib import Path
from rejection_reuse_v013588246 import RejectionReuse,normalize_concept_query,negative_signal_counts
class RejectionReuseTests(unittest.TestCase):
 def test_normalization(self):
  self.assertEqual(normalize_concept_query("宇宙を説明してください"),"宇宙")
  self.assertEqual(normalize_concept_query("宇宙とは"),"宇宙")
  self.assertEqual(normalize_concept_query("CPU"),"CPU")
 def test_cache_revision_and_evidence(self):
  with tempfile.TemporaryDirectory() as d:
   cache=RejectionReuse(Path(d)/"cache.jsonl")
   self.assertIsNone(cache.find("宇宙","証拠","model-A"))
   self.assertEqual(cache.record("宇宙","証拠","model-A","不適切","REJECT_NOT_ENTAILED"),"RECORDED")
   self.assertEqual(cache.record("宇宙","証拠","model-A","不適切","REJECT_NOT_ENTAILED"),"DUPLICATE")
   self.assertEqual(cache.find("宇宙","証拠","model-A")["candidate"],"不適切")
   self.assertIsNone(cache.find("宇宙","別の証拠","model-A"))
   self.assertIsNone(cache.find("宇宙","証拠","model-B"))
 def test_accept_not_cached(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):
    RejectionReuse(Path(d)/"cache").record("宇宙","証拠","model","正常","ACCEPT")
 def test_negative_stats(self):
  with tempfile.TemporaryDirectory() as d:
   self.assertEqual(negative_signal_counts(Path(d)/"missing.jsonl"),{"recorded":0,"not_trained":0})
if __name__=="__main__":unittest.main()
