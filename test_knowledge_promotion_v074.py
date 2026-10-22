import tempfile
import unittest
from pathlib import Path
from dual_semantic_memory_v071 import DualMemory
from knowledge_promotion_gate_v074 import promote
from evaluate_dual_adapter_v074 import evaluate_pairs
from dual_adapters_v073 import DualAdapterModel
from model import LanguageModel
import torch

class PromotionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        p=Path(self.tmp.name)
        self.m=DualMemory(p/"approved.jsonl",p/"candidate.jsonl")
        self.id=self.m.propose("問い","回答","external:1")
    def tearDown(self):self.tmp.cleanup()
    def test_no_implicit_approval(self):
        with self.assertRaises(ValueError):
            promote(self.m.approved_path,self.m.candidate_path,self.id,"reviewer","source","")
        self.assertIsNone(self.m.lookup_approved("問い"))
    def test_evidence_required(self):
        with self.assertRaises(ValueError):
            promote(self.m.approved_path,self.m.candidate_path,self.id,"reviewer","","APPROVE")
    def test_explicit_promotion_preserves_origin(self):
        result=promote(self.m.approved_path,self.m.candidate_path,self.id,"human","verified","APPROVE")
        self.assertFalse(result["weight_copied"])
        self.assertEqual(self.m.lookup_approved("問い")["source_id"],"external:1")
    def test_no_invalid_audit_destination(self):
        with self.assertRaises(ValueError):
            promote(self.m.approved_path,self.m.candidate_path,self.id,"human","verified","APPROVE",self.m.candidate_path)
        self.assertIsNone(self.m.lookup_approved("問い"))
    def test_unknown_id(self):
        with self.assertRaises(ValueError):
            promote(self.m.approved_path,self.m.candidate_path,"not-exists","human","verified","APPROVE")
    def test_adapter_routes_no_base_mutation(self):
        torch.manual_seed(4)
        base=LanguageModel(vocab_size=32,d_model=16,num_layers=1,hidden_dim=32,num_heads=2,context_length=8)
        model=DualAdapterModel(base,rank=4)
        x=torch.randint(0,32,(1,4))
        model.eval()
        with torch.no_grad():
            self.assertTrue(torch.allclose(model(x,"trusted"),model(x,"experimental")))
if __name__=="__main__":unittest.main()
