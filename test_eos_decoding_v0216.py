import unittest
import torch
from diagnose_eos_decoding_v0216 import next_step,aggregate

class EOSDecodingTests(unittest.TestCase):
    def test_greedy_eos_top(self):
        scores=torch.tensor([0.,3.,1.])
        tid,p,rank,selection=next_step(scores,[0],1,0,3,1.,torch.Generator().manual_seed(1))
        self.assertEqual(tid,1)
        self.assertEqual(rank,1)
        self.assertEqual(selection,1.)
    def test_greedy_eos_outside_top(self):
        scores=torch.tensor([3.,1.,2.])
        tid,p,rank,selection=next_step(scores,[0],1,0,3,1.,torch.Generator().manual_seed(1))
        self.assertNotEqual(tid,1)
        self.assertEqual(rank,3)
        self.assertEqual(selection,0.)
    def test_sampling_eos_excluded_by_top_k(self):
        scores=torch.tensor([4.,1.,3.])
        tid,p,rank,selection=next_step(scores,[0],1,.7,2,1.,torch.Generator().manual_seed(1))
        self.assertEqual(selection,0.)
        self.assertNotEqual(tid,1)
    def test_summary(self):
        samples=[{"prompt":"人: SFです","generated":"そう。","tokens":3,"terminated_by_eos":True,
          "eos_first_step_probability":.1,"eos_first_step_rank":2}]
        self.assertEqual(aggregate(samples)["eos_termination_fraction"],1.)
if __name__=="__main__":unittest.main()
