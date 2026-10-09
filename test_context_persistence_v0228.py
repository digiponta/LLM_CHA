import unittest
import torch
from context_persistence_loss_v0228 import persistence_loss

class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.logits=torch.zeros(2,8,11,requires_grad=True)
        self.targets=torch.tensor([[0,1,2,3,4,5,6,7],[0,1,2,3,4,5,6,7]])
        self.mask=torch.tensor([[0,1,1,1,1,1,0,0],[0,1,1,1,1,1,0,0]])
        self.flags=torch.tensor([True,False])
    def test_phase_counts(self):
        _,info=persistence_loss(self.logits,self.targets,self.mask,self.flags,init_k=2)
        self.assertEqual(info["init_tokens"],2)
        self.assertEqual(info["later_tokens"],3)
    def test_unmarked_rows_no_auxiliary_gradient(self):
        loss,_=persistence_loss(self.logits,self.targets,self.mask,self.flags,init_k=2)
        loss.backward()
        # Replay rows get only ordinary response loss, while padding and prompt get none.
        self.assertEqual(float(self.logits.grad[:,0,:].abs().sum()),0)
        self.assertEqual(float(self.logits.grad[:,6:,:].abs().sum()),0)
    def test_baseline(self):
        loss,info=persistence_loss(self.logits,self.targets,self.mask,self.flags,init_weight=0,late_weight=0)
        self.assertAlmostEqual(loss.item(),info["normal_loss"].item())
    def test_short_response_no_late(self):
        mask=self.mask.clone();mask[:,3:]=0
        _,info=persistence_loss(self.logits,self.targets,mask,self.flags,init_k=8)
        self.assertEqual(info["later_tokens"],0)
    def test_invalid_flags(self):
        with self.assertRaises(ValueError):
            persistence_loss(self.logits,self.targets,self.mask,torch.tensor([True]))
if __name__=="__main__":unittest.main()
