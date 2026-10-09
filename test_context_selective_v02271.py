import unittest
import torch
from context_selective_loss_v02271 import context_selective_loss


class ContextSelectiveTests(unittest.TestCase):
    def setUp(self):
        self.logits = torch.zeros(3, 5, 9, requires_grad=True)
        self.targets = torch.tensor([[1,2,3,4,5]] * 3)
        self.mask = torch.tensor([[0,1,1,1,0]] * 3)
        self.flags = torch.tensor([False, True, False])

    def test_only_context_selected(self):
        _, info = context_selective_loss(self.logits, self.targets, self.mask, self.flags, k=2)
        self.assertEqual(info["context_initial_tokens"], 2)

    def test_no_context_falls_back_to_normal(self):
        total, info = context_selective_loss(self.logits, self.targets, self.mask, torch.zeros(3, dtype=torch.bool))
        self.assertAlmostEqual(total.item(), info["normal_loss"].item())

    def test_weight_zero_matches_normal(self):
        total, info = context_selective_loss(self.logits, self.targets, self.mask, self.flags, weight=0)
        self.assertAlmostEqual(total.item(), info["normal_loss"].item())

    def test_gradients(self):
        total, _ = context_selective_loss(self.logits, self.targets, self.mask, self.flags)
        total.backward()
        self.assertEqual(float(self.logits.grad[:, 0].abs().sum()), 0)

    def test_bad_flags(self):
        with self.assertRaises(ValueError):
            context_selective_loss(self.logits, self.targets, self.mask, torch.tensor([True]))

if __name__ == "__main__":
    unittest.main()
