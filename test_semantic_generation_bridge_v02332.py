import unittest,torch
from model import LanguageModel
from semantic_generation_bridge_v02332 import semantic_vector,Bridge,bridge_logits,features
class BridgeTests(unittest.TestCase):
    def test_semantic_deterministic(self):
        a=semantic_vector("LLM",["learning"],"UNSPECIFIED")
        b=semantic_vector("LLM",["learning"],"UNSPECIFIED")
        self.assertTrue(torch.equal(a,b))
        self.assertEqual(a.shape,(64,))
        self.assertFalse(torch.equal(a,semantic_vector("LLM",["development"])))
    def test_zero_initialization_is_noop(self):
        model=LanguageModel(vocab_size=64,d_model=16,num_layers=1,hidden_dim=32,num_heads=2,context_length=64)
        bridge=Bridge(16)
        x=torch.tensor([[1,2,3]])
        model.eval()
        with torch.no_grad():
            self.assertTrue(torch.allclose(bridge_logits(model,bridge,x,semantic_vector("LLM",["learning"]).unsqueeze(0)),model(x)))
    def test_bridge_gradient(self):
        model=LanguageModel(vocab_size=64,d_model=16,num_layers=1,hidden_dim=32,num_heads=2,context_length=64)
        for p in model.parameters():p.requires_grad_(False)
        bridge=Bridge(16)
        x=torch.tensor([[1,2,3]])
        logits=bridge_logits(model,bridge,x,semantic_vector("LLM",["learning"]).unsqueeze(0))
        logits.sum().backward()
        self.assertIsNotNone(bridge.projector.weight.grad)
        self.assertTrue(all(p.grad is None for p in model.parameters()))
    def test_feature_extraction(self):
        row={"canonical":{"topic":"LLM","purposes":["learning","development"],"relation":"SEQUENTIAL"}}
        self.assertEqual(features(row).shape,(64,))
if __name__=="__main__":unittest.main()
