import unittest
from train_controlled_replay_v0135858 import replay_allocation
from train_independent_controls_v0135857 import allocation
class TestBudget(unittest.TestCase):
 def test_zero(self):self.assertEqual(replay_allocation(8000,0),0)
 def test_quarter(self):self.assertEqual(replay_allocation(8000,0.25),2667)
 def test_half(self):self.assertEqual(replay_allocation(8000,0.5),8000)
 def test_reject(self):
  with self.assertRaises(ValueError):replay_allocation(8000,0.75)
 def test_train_update_allocation(self):
  for n in (20,40,80):
   self.assertEqual(sum(allocation(8000,n)),8000)
if __name__=="__main__":unittest.main()
