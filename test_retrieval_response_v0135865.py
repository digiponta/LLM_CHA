import unittest
from compare_retrieval_response_v0135865 import decide,encode_context
class Tests(unittest.TestCase):
 def setUp(self):
  self.h=[{"id":"ok","question":"眠たい","answer":"休もう","score":0.91,"adjusted_score":0.91},
          {"id":"other","question":"暇だ","answer":"そう","score":0.89,"adjusted_score":0.88}]
 def test_accepted(self):
  self.assertTrue(decide(self.h,.85,.01)["accepted"])
 def test_unknown_low_score(self):
  self.assertFalse(decide(self.h,.95)["accepted"])
 def test_ambiguous_margin(self):
  self.assertFalse(decide(self.h,.85,.05)["accepted"])
 def test_no_candidates(self):
  self.assertEqual(decide([])["reason"],"NO_CANDIDATES")
 def test_reference_not_in_context(self):
  ctx=encode_context("眠くて集中できない",self.h[0])
  self.assertIn("眠くて集中できない",ctx)
  self.assertIn("休もう",ctx)
  self.assertNotIn("評価用正解",ctx)
if __name__=="__main__":unittest.main()
