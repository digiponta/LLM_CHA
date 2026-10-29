import unittest
from train_independent_controls_v0135857 import allocation,choose_masks
class Tests(unittest.TestCase):
 def test_exact_budget(self):
  for b,u in ((8000,20),(8000,40),(7921,30),(12,12)):
   z=allocation(b,u)
   self.assertEqual(sum(z),b)
   self.assertEqual(len(z),u)
   self.assertLessEqual(max(z)-min(z),1)
 def test_invalid_budget(self):
  with self.assertRaises(ValueError):allocation(5,6)
 def test_repeated_supervised_positions(self):
  import torch
  m=torch.tensor([[0,1,1,0],[0,1,0,0]],dtype=torch.float32)
  grouped,next_cursor=choose_masks(m,8,0)
  self.assertEqual(sum(len(v) for v in grouped.values()),8)
  self.assertEqual(next_cursor,2)
  self.assertEqual(set(grouped),{0,1})
if __name__=="__main__":unittest.main()
