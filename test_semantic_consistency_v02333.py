import unittest,torch
from model import LanguageModel
from semantic_generation_bridge_v02332 import Bridge,semantic_vector
from semantic_consistency_training_v02333 import step_loss,prepare
class ConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.model=LanguageModel(vocab_size=64,d_model=16,num_layers=1,hidden_dim=32,num_heads=2,context_length=64)
        for p in self.model.parameters():p.requires_grad_(False)
        self.model.eval()
        self.bridge=Bridge(16)
        s1=semantic_vector("LLM",["learning"])
        s2=semantic_vector("LLM",["development"])
        self.p= (torch.tensor([[1,5,6]]),torch.tensor([-100,7,8]),s1,("learning",),"one")
        self.n= (torch.tensor([[1,5,6]]),torch.tensor([-100,7,8]),s2,("development",),"two")
    def test_zero_weight_reduces_to_lm(self):
        total,pos,neg,contrast=step_loss(self.model,self.bridge,self.p,self.n,weight=0)
        self.assertTrue(torch.allclose(total,pos))
        self.assertTrue(torch.isfinite(contrast))
    def test_contrastive_gradient(self):
        total,*_=step_loss(self.model,self.bridge,self.p,self.n,weight=1)
        total.backward()
        self.assertIsNotNone(self.bridge.projector.weight.grad)
        self.assertTrue(torch.isfinite(self.bridge.projector.weight.grad).all())
        self.assertTrue(all(p.grad is None for p in self.model.parameters()))
    def test_same_semantics_initially_equal(self):
        _,positive,wrong,_=step_loss(self.model,self.bridge,self.p,self.n)
        self.assertAlmostEqual(positive.item(),wrong.item(),places=5)
if __name__=="__main__":unittest.main()
