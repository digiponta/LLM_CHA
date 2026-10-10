import unittest
import torch
from model import LanguageModel
from relative_monotonic_pointer_v023328 import (
    PositionPointer,MODES,decode,evaluate,train
)
class RelativeMonotonicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.manual_seed(428)
        cls.model=LanguageModel(vocab_size=120,d_model=16,num_layers=2,hidden_dim=32,
            num_heads=2,causal=True,context_length=80,use_position_embedding=True).eval()
        for p in cls.model.parameters():p.requires_grad_(False)
    def test_all_modes_and_shapes(self):
        self.assertEqual(set(MODES),{"baseline","relative","monotonic","combined"})
        for mode in MODES:
            head=PositionPointer(16,mode)
            scores=head.position_logits(self.model,[10,11],[10],7,2)
            self.assertEqual(scores.shape,(3,))
            self.assertTrue(torch.isfinite(scores).all())
    def test_forward_and_gradients(self):
        for mode in MODES:
            head=PositionPointer(16,mode)
            loss=head.loss_for(self.model,[10,11],7,2,3)
            loss.backward()
            self.assertTrue(any(p.grad is not None and p.grad.abs().sum()>0 for p in head.parameters()))
        self.assertTrue(all(p.grad is None for p in self.model.parameters()))
    def test_predict_without_gold_alignment(self):
        head=PositionPointer(16,"combined")
        got=decode(self.model,head,[10,11],7,2,3)
        self.assertTrue(set(got)<=set([10,11,3]))
        self.assertLessEqual(len(got),32)
    def test_evaluation(self):
        head=PositionPointer(16,"baseline")
        r=evaluate(self.model,head,[[10,11],[11,10]],7,2,3)
        self.assertEqual(r["total"],2)
        self.assertTrue(0<=r["teacher_position_accuracy"]<=1)
        self.assertEqual(r["by_position"]["0"]["total"],2)
    def test_invalid_mode(self):
        with self.assertRaises(ValueError):PositionPointer(16,"position_oracle")
if __name__=="__main__":unittest.main()
