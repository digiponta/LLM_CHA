import unittest
from measure_four_axes_v0135855 import exact_stats,validate_split
class Tests(unittest.TestCase):
 def test_generation_counts(self):
  samples=[{"token_exact_body":True,"raw_exact":False,"nfkc_equal":True},
           {"token_exact_body":False,"raw_exact":False,"nfkc_equal":False}]
  self.assertEqual(exact_stats(samples),{"exact":1,"raw_exact":0,"nfkc_exact":1,"total":2})
 def test_non_overlapping_splits(self):
  validate_split([{"user":"q1"}],[{"user":"q2"}],[{"user":"q3"}])
 def test_leakage_rejected(self):
  with self.assertRaises(ValueError):
   validate_split([{"user":"q1"}],[{"user":"q1"}],[{"user":"q3"}])
if __name__=="__main__":unittest.main()
