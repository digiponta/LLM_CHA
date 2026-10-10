import unittest
import torch
from model import LanguageModel
from pointer_copy_v023325 import PointerHead
from adaptive_pointer_length_v023326 import AdaptiveHead,prepare,sequences,position_diagnostics
class AdaptivePointerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.manual_seed(26)
        cls.model=LanguageModel(vocab_size=120,d_model=16,num_layers=2,hidden_dim=32,
            num_heads=2,causal=True,context_length=80,use_position_embedding=True).eval()
        for param in cls.model.parameters():param.requires_grad_(False)
    def test_splits(self):
        a=prepare(42,list(range(8,72)),list(range(72,88)),20,8,8)
        self.assertEqual(len(a["train_short"]),20)
        self.assertEqual(len(a["train_long"]),20)
        self.assertEqual(len(a["long"]),40)
        self.assertEqual(len(a["novel_extra"]),40)
        all_sequences=[tuple(v) for group in a.values() for v in group]
        self.assertEqual(len(all_sequences),len(set(all_sequences)))
    def test_adaptive_probs(self):
        head=AdaptiveHead(16)
        prob,logits=head.distribution(self.model,[10,11],[10],7,2,3)
        self.assertAlmostEqual(float(prob.detach().sum()),1.,places=5)
        self.assertEqual(len(logits),3)
    def test_adaptive_gradient_head_only(self):
        head=AdaptiveHead(16)
        head.loss_for(self.model,[10,11],7,2,3).backward()
        self.assertIsNotNone(head.gate[0].weight.grad)
        self.assertTrue(any(p.grad is not None and p.grad.abs().sum()>0 for p in head.parameters()))
        self.assertTrue(all(p.grad is None for p in self.model.parameters()))
    def test_position_report(self):
        head=PointerHead(16,"pointer")
        result=position_diagnostics(self.model,head,[[10,11]],7,2,3)
        self.assertEqual(result["total"],1)
        self.assertEqual(len(result["cases"][0]["steps"]),3)
        self.assertTrue(0<=result["teacher_pointer_position_accuracy"]<=1)
    def test_invalid_sequence(self):
        with self.assertRaises(ValueError):sequences(42,[10],0,2,3)
if __name__=="__main__":unittest.main()
