import unittest
import torch
from model import LanguageModel
from audit_core_integrity_v0135815 import model_diagnostics,source_report

class CoreIntegrityTests(unittest.TestCase):
    def test_causal_future_independence(self):
        torch.manual_seed(10)
        m=LanguageModel(vocab_size=32,d_model=16,num_layers=2,
            hidden_dim=32,num_heads=4,context_length=16)
        r=model_diagnostics(m,torch.device("cpu"))
        self.assertTrue(r["causality_smoke_pass"],r)
    def test_position_flag_off(self):
        m=LanguageModel(vocab_size=32,d_model=16,num_layers=1,
             hidden_dim=32,num_heads=4,context_length=16)
        self.assertFalse(model_diagnostics(m,torch.device("cpu"))["position_embedding_enabled"])
    def test_position_flag_on(self):
        m=LanguageModel(vocab_size=32,d_model=16,num_layers=1,
             hidden_dim=32,num_heads=4,context_length=16,use_position_embedding=True)
        self.assertTrue(model_diagnostics(m,torch.device("cpu"))["position_embedding_enabled"])
    def test_train_probe_format_mismatch(self):
        self.assertFalse(source_report()["format_match"])
    def test_all_token_loss(self):
        self.assertFalse(source_report()["assistant_only_loss"])
if __name__=="__main__":unittest.main()
