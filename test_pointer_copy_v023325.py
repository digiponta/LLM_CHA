import unittest
import torch
from model import LanguageModel
from pointer_copy_v023325 import PointerHead,predict,evaluate,fit_head

class PointerCopyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.manual_seed(123)
        cls.base=LanguageModel(vocab_size=120,d_model=16,num_layers=2,hidden_dim=32,
            num_heads=2,causal=True,context_length=80,use_position_embedding=True).eval()
        for p in cls.base.parameters():p.requires_grad_(False)
    def test_probability_normalization(self):
        for mode in ("pointer","hybrid"):
            head=PointerHead(16,mode)
            prob,logits=head.distribution(self.base,[10,11,10],[10],7,2,3)
            self.assertAlmostEqual(float(prob.sum()),1.,places=5)
            self.assertEqual(len(logits),4)
            self.assertGreaterEqual(float(prob[10]),0.)
    def test_pointer_cannot_emit_outside_source_or_eos(self):
        head=PointerHead(16,"pointer")
        prob,_=head.distribution(self.base,[10,11],[10],7,2,3)
        self.assertEqual(int(torch.count_nonzero(prob)),3)
    def test_training_gradient_is_head_only(self):
        head=PointerHead(16,"pointer")
        loss=head.loss_for(self.base,[10,11],7,2,3)
        loss.backward()
        self.assertTrue(any(p.grad is not None and p.grad.abs().sum()>0 for p in head.parameters()))
        self.assertTrue(all(p.grad is None for p in self.base.parameters()))
    def test_hybrid_gradient(self):
        head=PointerHead(16,"hybrid")
        head.loss_for(self.base,[10,11],7,2,3).backward()
        self.assertIsNotNone(head.gate.weight.grad)
    def test_generation_is_not_given_positions(self):
        for mode in ("pointer","hybrid"):
            head=PointerHead(16,mode)
            seq=predict(self.base,head,[10,11],7,2,3,budget=5)
            self.assertLessEqual(len(seq),5)
    def test_invalid_mode(self):
        with self.assertRaises(ValueError):PointerHead(16,"oracle")
if __name__=="__main__":unittest.main()
