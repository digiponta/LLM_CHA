import unittest
import torch
from model import LanguageModel
from audit_llm_core_v023312 import order_sensitivity

class CoreAuditTests(unittest.TestCase):
    def test_default_position_disabled_is_explicit(self):
        model=LanguageModel(vocab_size=32,d_model=16,num_layers=1,hidden_dim=32,num_heads=4,context_length=16)
        self.assertIsNone(model.position_embedding)
        self.assertFalse(model.config()["use_position_embedding"])
    def test_configured_position_enabled(self):
        model=LanguageModel(vocab_size=32,d_model=16,num_layers=1,hidden_dim=32,num_heads=4,context_length=16,use_position_embedding=True)
        self.assertIsNotNone(model.position_embedding)
        self.assertTrue(model.config()["use_position_embedding"])
    def test_single_block_permutation_invariance_without_positions(self):
        torch.manual_seed(73)
        model=LanguageModel(vocab_size=32,d_model=16,num_layers=1,hidden_dim=32,num_heads=4,context_length=16,use_position_embedding=False)
        delta=order_sensitivity(model,[1,2,3,4],[3,2,1,4])
        self.assertLess(delta["max_abs_logit_delta"],1e-5)
    def test_causal_mask_used(self):
        model=LanguageModel(vocab_size=32,d_model=16,num_layers=2,hidden_dim=32,num_heads=4,context_length=16)
        self.assertTrue(all(block.attention.causal for block in model.blocks))
if __name__=="__main__":unittest.main()
