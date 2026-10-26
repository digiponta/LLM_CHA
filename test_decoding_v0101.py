"""Tiny deterministic decoder smoke tests; no real checkpoint is needed."""
import unittest
from unittest.mock import patch
import torch
from semantic_decode_v0101 import decode, _penalize, _score
from evaluate_decoding_v0101 import prefix_length

class TinyTokenizer:
    eos_id = 3
    def encode(self, text, add_bos=False):
        if text == "p":
            return [0]
        return [1, 2]
    def decode(self, ids, skip_special_tokens=True):
        return "".join({0: "", 1: "A", 2: "B", 3: ""}.get(i, "") for i in ids)

class TinyModel(torch.nn.Module):
    context_length = 16
    def __init__(self):
        super().__init__()
        self.p = torch.nn.Parameter(torch.zeros(1))
    def forward(self, x):
        # Deterministic logits, EOS eventually terminates.
        logits = torch.tensor([0., 3., 2., 1.], device=x.device)
        if x.shape[1] >= 3:
            logits = torch.tensor([0., -5., -5., 5.], device=x.device)
        return logits.reshape(1, 1, -1)

class DecodeTests(unittest.TestCase):
    def setUp(self):
        self.model, self.tokenizer = TinyModel(), TinyTokenizer()
    def test_greedy(self):
        self.assertTrue(decode(self.model, self.tokenizer, "p", beam_width=1).text)
    def test_beam(self):
        self.assertTrue(decode(self.model, self.tokenizer, "p", beam_width=3).text)
    def test_penalty_sign(self):
        a = torch.tensor([2., -2.])
        b = _penalize(a, [0, 1], 2)
        self.assertEqual(b.tolist(), [1., -4.])
    def test_length_normalization(self):
        self.assertEqual(_score(-4., 2, 0), -4.)
    def test_prefix(self):
        self.assertEqual(prefix_length([1, 2, 4], [1, 2, 5]), 2)
    def test_no_reference_to_decoder(self):
        with patch("evaluate_decoding_v0101.decode") as mock:
            mock.return_value = type("R", (), dict(text="A", token_ids=[1], elapsed_ms=1., score=-1.))()
            from evaluate_decoding_v0101 import evaluate
            evaluate(self.model, self.tokenizer, [{"id": "x", "prompt": "p", "reference": "secret"}],
                     configurations=[("greedy", 1, 1., 1., 2)])
            self.assertNotIn("reference", mock.call_args.kwargs)
            self.assertNotIn("secret", mock.call_args.args)

if __name__ == "__main__":
    unittest.main()
