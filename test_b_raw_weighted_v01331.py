import unittest
import torch
from online_train import weighted_answer_mask
from train_b_raw_weighted_v01331 import VARIANTS, plan
from evaluate_b_raw_weighted_v01331 import aggregate
from pathlib import Path

class WeightedAnswerLossTests(unittest.TestCase):
    def test_first_answer_token_only(self):
        mask=torch.tensor([[0.,0.,1.,1.,1.,0.]])
        out=weighted_answer_mask(mask,1,4.)
        self.assertEqual(out.tolist(),[[0.,0.,4.,1.,1.,0.]])
    def test_first_eight_and_padding(self):
        mask=torch.tensor([[0.,1.,1.,1.,0.]])
        self.assertEqual(weighted_answer_mask(mask,8,4.).tolist(),[[0.,4.,4.,4.,0.]])
    def test_standard_unchanged(self):
        m=torch.tensor([[0.,1.,1.]])
        self.assertTrue(torch.equal(weighted_answer_mask(m),m))
    def test_invalid(self):
        with self.assertRaises(ValueError):weighted_answer_mask(torch.ones(1,3),1,.5)
    def test_isolated_variants(self):
        self.assertEqual(len(VARIANTS),3)
        self.assertEqual(len({x["checkpoint"] for x in plan(Path("results/test"))}),3)
    def test_summary(self):
        d=aggregate([{"first_rank":1,"first_nll":2,"answer_nll":3}])
        self.assertEqual(d["first_rank1"],1)

if __name__=="__main__":unittest.main()
