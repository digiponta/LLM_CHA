import unittest
import torch
from model import LanguageModel
from dual_adapters_v073 import DualAdapterModel
from diagnose_generation_v076 import probe

class FakeTokenizer:
    eos_id=1
    def encode(self,text,add_bos=False,add_eos=False):
        ids=[2,3,4] if text.startswith("人:") else [5,6]
        if add_bos:ids=[0]+ids
        if add_eos:ids=ids+[1]
        return ids
    def decode(self,ids):
        return "".join(str(x) for x in ids)

class DiagnosticTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(10)
        self.model=DualAdapterModel(LanguageModel(vocab_size=16,d_model=12,
            num_layers=1,hidden_dim=24,num_heads=2,context_length=8),rank=3)
        self.tokenizer=FakeTokenizer()
    def test_all_routes_report_rank(self):
        for route in ("base","trusted","experimental"):
            result=probe(self.model,self.tokenizer,"test","56",route,max_new_tokens=3)
            self.assertGreaterEqual(result["first_reference_token_rank"],1)
            self.assertLessEqual(result["first_reference_token_rank"],16)
            self.assertIn(result["stop_reason"],("eos","token_limit"))
    def test_invalid_route(self):
        with self.assertRaises(ValueError):
            probe(self.model,self.tokenizer,"test","56","unknown")
    def test_frozen_model(self):
        self.assertTrue(all(not p.requires_grad for p in self.model.base.parameters()))
    def test_empty_answer_rejected(self):
        class EmptyTokenizer(FakeTokenizer):
            def encode(self,text,add_bos=False,add_eos=False):return []
        with self.assertRaises(ValueError):
            probe(self.model,EmptyTokenizer(),"test","", "base")
if __name__=="__main__":unittest.main()
