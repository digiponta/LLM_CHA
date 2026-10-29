import unittest
from audit_generation_quality_v0135860 import auto_metrics,score
class Tests(unittest.TestCase):
 def test_garbled(self):
  self.assertEqual(auto_metrics("あ�")["replacement_characters"],1)
 def test_repetition(self):
  self.assertGreater(auto_metrics("abcabcabcabc")["max_4gram_repetition"],2)
 def test_missing_human_review(self):
  self.assertEqual(score({"id":"x","relevance":""}),{})
 def test_reject_invalid_rating(self):
  with self.assertRaises(ValueError):score({"id":"x","relevance":"6"})
if __name__=="__main__":unittest.main()
