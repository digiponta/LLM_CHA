import unittest
import torch
from model import LanguageModel
from verify_llm_core_functional_v023313 import causal_isolation,next_token_consistency,checkpoint_roundtrip

class FunctionalCoreTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(7)
        self.model=LanguageModel(vocab_size=32,d_model=16,num_layers=2,hidden_dim=32,
                                 num_heads=4,context_length=32,use_position_embedding=True)
        self.ids=[2,3,4,5,6]
    def test_causal_isolation(self):
        self.assertLess(causal_isolation(self.model,self.ids),1e-5)
    def test_greedy_forward_parity(self):
        result=next_token_consistency(self.model,self.ids)
        self.assertTrue(result["greedy_matches_forward"])
        self.assertLess(result["max_logit_delta"],1e-6)
    def test_checkpoint_roundtrip(self):
        self.assertLess(checkpoint_roundtrip(self.model,self.ids),1e-6)
    def test_generate_does_not_change_checkpoint(self):
        state={k:v.detach().clone() for k,v in self.model.state_dict().items()}
        self.model.generate(self.ids,max_new_tokens=3,temperature=0,repetition_penalty=1.)
        self.assertTrue(all(torch.equal(v,self.model.state_dict()[k]) for k,v in state.items()))
if __name__=="__main__":unittest.main()
