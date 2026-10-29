import unittest
from analyze_four_axes_v0135856 import select_at_budget
class Tests(unittest.TestCase):
 def test_select_prior_measurement(self):
  rows=[{"supervised_token_exposures":0,"step":0},{"supervised_token_exposures":2000,"step":10},{"supervised_token_exposures":4000,"step":20}]
  self.assertEqual(select_at_budget(rows,3500)["step"],10)
 def test_exact_budget(self):
  rows=[{"supervised_token_exposures":0,"step":0},{"supervised_token_exposures":2000,"step":10}]
  self.assertEqual(select_at_budget(rows,2000)["step"],10)
 def test_invalid_budget(self):
  with self.assertRaises(ValueError):select_at_budget([{"supervised_token_exposures":0}],-1)
if __name__=="__main__":unittest.main()
