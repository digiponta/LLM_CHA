import unittest
from evidence_candidate_analysis_v013588237 import analyze
class CandidateAnalysisTests(unittest.TestCase):
 def test_exact(self):
  a=analyze("宇宙は膨張している。",{"topic":"宇宙","excerpt":"宇宙は膨張している。","url":"https://example.org"},"ACCEPT_SOURCE_EXTRACT")
  self.assertTrue(a["candidate_sentences"][0]["exact_source_substring"])
 def test_nonmatch(self):
  a=analyze("宇宙は収縮する。",{"excerpt":"宇宙は膨張している。"},"REJECT_NOT_ENTAILED")
  self.assertFalse(a["candidate_sentences"][0]["exact_source_substring"])
 def test_empty(self):
  a=analyze("",{"excerpt":""},"REJECT_UNKNOWN")
  self.assertEqual(a["candidate_sentences"],[])
 def test_no_semantic_claim(self):
  a=analyze("別表現",{"excerpt":"根拠の文"},"REJECT_NOT_ENTAILED")
  self.assertIn("no semantic entailment",a["interpretation"])
if __name__=="__main__":unittest.main()
