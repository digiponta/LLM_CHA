import unittest
import torch
from diagnose_eos_continuation_v02282 import select_token
class EOSTests(unittest.TestCase):
    def setUp(self):
        self.logits=torch.tensor([0.0,1.0,3.0,2.0])
    def test_greedy_eos(self):
        chosen,t=select_token(self.logits,"greedy",0,2)
        self.assertEqual(chosen,2)
        self.assertFalse(t["eos_suppressed"])
    def test_suppress_early(self):
        chosen,t=select_token(self.logits,"no_eos_16",0,2)
        self.assertEqual(chosen,3)
        self.assertTrue(t["eos_suppressed"])
        self.assertEqual(t["top1_id"],2)
    def test_release_at_boundary(self):
        chosen,t=select_token(self.logits,"no_eos_16",16,2)
        self.assertEqual(chosen,2)
    def test_eos_rank(self):
        _,t=select_token(self.logits,"greedy",0,2)
        self.assertEqual(t["eos_rank"],1)
if __name__=="__main__":unittest.main()
