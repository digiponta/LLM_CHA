import unittest
import torch
from model import LanguageModel
from diagnose_copy_mechanism_v023323 import (
    output_context,next_logits,copy_probability,intervention,
    attention_snapshot,inspect_attention,eos_probe
)
class MechanismTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.manual_seed(7)
        cls.model=LanguageModel(vocab_size=120,d_model=16,num_layers=2,hidden_dim=32,
                                num_heads=2,causal=True,context_length=64,
                                use_position_embedding=True).eval()
    def test_context(self):
        self.assertEqual(output_context([10,11],[10],7,2),[2,7,10,11,7,10])
    def test_next_logits_match_forward(self):
        ctx=[2,7,10,11,7]
        direct=self.model(torch.tensor([ctx]))[0,-1]
        self.assertTrue(torch.allclose(direct,next_logits(self.model,ctx)))
    def test_intervention_changes_only_source(self):
        result=intervention(self.model,[10,11],1,88,7,2)
        self.assertEqual((result["old_id"],result["new_id"]),(11,88))
        self.assertTrue(0<=result["new_id_probability_after"]<=1)
        self.assertTrue(0<=result["new_id_logit_rank_after"]<=120)
        with self.assertRaises(ValueError):
            intervention(self.model,[10,11],1,11,7,2)
    def test_attention_distribution(self):
        ctx=output_context([10,11],[10],7,2)
        weights=attention_snapshot(self.model,ctx)
        self.assertEqual(len(weights),2)
        self.assertEqual(len(weights[0]),2)
        for layer in weights:
            for head in layer:
                self.assertAlmostEqual(sum(head),1,places=5)
        matched=inspect_attention(self.model,[10,11],1,7,2)
        self.assertEqual(len(matched),2)
        self.assertEqual(len(matched[0]["heads"]),2)
    def test_eos(self):
        result=eos_probe(self.model,[10,11],7,2,3)
        self.assertEqual(len(result["precompletion"]),2)
        self.assertTrue(0<=result["final_eos_probability"]<=1)
if __name__=="__main__":unittest.main()
