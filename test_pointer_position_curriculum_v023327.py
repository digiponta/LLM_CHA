import unittest
import torch
from model import LanguageModel
from pointer_copy_v023325 import PointerHead
from adaptive_pointer_length_v023326 import prepare,sequences
from pointer_position_curriculum_v023327 import position_profile,evaluate_stage,loss_mean

class PointerStageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.manual_seed(327)
        cls.model=LanguageModel(vocab_size=120,d_model=16,num_layers=2,hidden_dim=32,
            num_heads=2,causal=True,context_length=80,use_position_embedding=True).eval()
        for x in cls.model.parameters():x.requires_grad_(False)
        cls.head=PointerHead(16,"pointer").eval()
    def test_independent_long_validation(self):
        data=prepare(42,list(range(8,72)),list(range(72,88)),20,8,8)
        exclusion=[s for group in data.values() for s in group]
        longval=sequences(1041,list(range(8,72)),8,12,18,exclusion)
        self.assertEqual(len(longval),8)
        self.assertTrue(all(12<=len(x)<=18 for x in longval))
        self.assertFalse(set(map(tuple,longval))&set(map(tuple,exclusion)))
    def test_position_profile_counts(self):
        p=position_profile(self.model,self.head,[[10,11],[11,10,11]],7,2,3)
        self.assertEqual(sum(x["total"] for x in p["by_position"].values()),7)
        self.assertEqual(p["by_repetition"]["repeat"]["total"],4)
        self.assertEqual(p["by_repetition"]["unique"]["total"],3)
    def test_stage_report(self):
        x=evaluate_stage(self.model,self.head,[[10,11]],7,2,3)
        self.assertEqual(x["total"],1)
        self.assertIn("teacher_eos_accuracy",x)
        self.assertIn("by_position",x)
    def test_validation_loss(self):
        x=loss_mean(self.model,self.head,[[10,11],[11,10]],7,2,3)
        self.assertGreaterEqual(x,0)
    def test_no_backbone_gradient(self):
        self.head.loss_for(self.model,[10,11],7,2,3).backward()
        self.assertTrue(all(x.grad is None for x in self.model.parameters()))
if __name__=="__main__":unittest.main()
