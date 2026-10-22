import unittest
import torch
from model import LanguageModel
from dual_adapters_v073 import DualAdapterModel,frozen_digest,masked_cross_entropy

class DualAdaptersTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(7)
        self.base=LanguageModel(vocab_size=32,d_model=16,num_layers=1,hidden_dim=32,num_heads=2,context_length=8)
        self.model=DualAdapterModel(self.base,rank=4)
    def test_base_frozen(self):
        self.assertTrue(all(not p.requires_grad for p in self.base.parameters()))
        self.assertTrue(all(p.requires_grad for p in self.model.training_parameters("experimental")))
    def test_routes_initially_equal(self):
        ids=torch.randint(0,32,(2,5))
        self.assertTrue(torch.allclose(self.model(ids,"experimental"),self.model(ids,"trusted")))
    def test_experimental_update_isolated(self):
        h=frozen_digest(self.base)
        trusted=self.model.export_adapter("trusted")
        ids=torch.randint(0,32,(1,5))
        y=torch.randint(0,32,(1,5))
        opt=torch.optim.AdamW(self.model.training_parameters("experimental"),lr=0.01)
        for _ in range(2):
            opt.zero_grad()
            loss=masked_cross_entropy(self.model(ids),y,torch.ones_like(y,dtype=torch.float))
            loss.backward()
            opt.step()
        self.assertEqual(frozen_digest(self.base),h)
        self.assertTrue(all(torch.equal(v,self.model.export_adapter("trusted")[k]) for k,v in trusted.items()))
        self.assertTrue(any(torch.any(v!=0) for k,v in self.model.export_adapter("experimental").items() if k.startswith("up")))
    def test_invalid_route_rejected(self):
        with self.assertRaises(ValueError):
            self.model(torch.randint(0,32,(1,3)),route="approved-or-unapproved")
    def test_train_keeps_base_eval(self):
        self.model.train()
        self.assertFalse(self.base.training)
if __name__=="__main__":unittest.main()
