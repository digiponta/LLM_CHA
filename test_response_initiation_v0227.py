import unittest
import torch
from response_initiation_v0227 import initiation_loss


class ResponseInitiationTests(unittest.TestCase):
    def setUp(self):
        self.logits = torch.zeros(2, 5, 7, requires_grad=True)
        self.targets = torch.tensor([[1, 2, 3, 4, -100], [1, 2, 3, 4, 5]])
        self.mask = torch.tensor([[0, 1, 1, 1, 0], [0, 0, 1, 1, 1]])

    def test_first_k_per_sequence(self):
        loss, values = initiation_loss(self.logits, self.targets, self.mask, k=2)
        self.assertEqual(values["initial_tokens"], 4)
        self.assertEqual(values["response_tokens"], 6)
        self.assertAlmostEqual(loss.item(), 1.5 * torch.log(torch.tensor(7.)).item(), places=5)

    def test_weight_zero_is_baseline(self):
        _, values = initiation_loss(self.logits, self.targets, self.mask, k=4, weight=0)
        base, _ = initiation_loss(self.logits, self.targets, self.mask, k=2, weight=0)
        self.assertAlmostEqual(base.item(), values["normal_loss"].item())

    def test_differentiable(self):
        loss, _ = initiation_loss(self.logits, self.targets, self.mask)
        loss.backward()
        self.assertIsNotNone(self.logits.grad)
        self.assertEqual(self.logits.grad[0, 0].abs().sum().item(), 0)

    def test_empty_response_rejected(self):
        with self.assertRaises(ValueError):
            initiation_loss(self.logits, self.targets, torch.zeros_like(self.mask))

    def test_no_prompt_leakage(self):
        original, _ = initiation_loss(self.logits, self.targets, self.mask)
        changed = self.targets.clone()
        changed[self.mask == 0] = 6
        updated, _ = initiation_loss(self.logits, changed, self.mask)
        self.assertAlmostEqual(original.item(), updated.item())


if __name__ == "__main__":
    unittest.main()
