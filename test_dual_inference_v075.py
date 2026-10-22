import unittest
import torch
from model import LanguageModel
from dual_adapters_v073 import DualAdapterModel
from dual_inference_v075 import route,generate

class RouteTests(unittest.TestCase):
    def test_normal_is_trusted(self):
        self.assertEqual(route("normal"),"trusted")
        self.assertEqual(route("normal",True),"trusted")
    def test_experiment_denied_by_default(self):
        with self.assertRaises(ValueError):route("experiment")
    def test_explicit_optin(self):
        self.assertEqual(route("experiment",True),"experimental")
    def test_invalid_mode(self):
        with self.assertRaises(ValueError):route("unknown",True)
    def test_generation_routes(self):
        torch.manual_seed(3)
        model=DualAdapterModel(LanguageModel(vocab_size=24,d_model=12,
            num_layers=1,hidden_dim=24,num_heads=2,context_length=8),rank=3)
        class FakeTokenizer:
            eos_id=1
            def encode(self,txt,add_bos=False):return [2,3,4]
            def decode(self,ids):return ",".join(map(str,ids))
        t=FakeTokenizer()
        outputs=[generate(model,t,"test",r,3) for r in ("base","trusted","experimental")]
        self.assertEqual(outputs[0],outputs[1])
        self.assertEqual(outputs[1],outputs[2])
    def test_generation_bad_route(self):
        model=DualAdapterModel(LanguageModel(vocab_size=24,d_model=12,
            num_layers=1,hidden_dim=24,num_heads=2,context_length=8),rank=3)
        with self.assertRaises(ValueError):generate(model,None,"hello","unapproved")
if __name__=="__main__":unittest.main()
