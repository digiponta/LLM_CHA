import unittest,random
import torch
from model import LanguageModel
from decoupled_eos_rollout_v023330 import DecoupledHead,MODES,training_loss,decode,evaluate,rollout_history

class EOSRolloutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.manual_seed(330)
        cls.model=LanguageModel(vocab_size=120,d_model=16,num_layers=2,hidden_dim=32,
            num_heads=2,causal=True,context_length=80,use_position_embedding=True).eval()
        for param in cls.model.parameters():param.requires_grad_(False)
    def test_modes(self):
        self.assertEqual(set(MODES),{"combined","decoupled","rollout","decoupled_rollout"})
    def test_position_and_eos_logit_shapes(self):
        for sep in (False,True):
            head=DecoupledHead(16,decoupled=sep)
            logits=head.position_logits(self.model,[10,11],[10],7,2)
            self.assertEqual(tuple(logits.shape),(3,))
            self.assertTrue(torch.isfinite(logits).all())
    def test_free_decode_and_eos(self):
        for sep in (False,True):
            head=DecoupledHead(16,decoupled=sep)
            result=decode(self.model,head,[10,11],7,2,3,budget=8)
            self.assertLessEqual(len(result),8)
            self.assertTrue(set(result)<={10,11,3})
    def test_rollout_history_has_no_eos(self):
        head=DecoupledHead(16,decoupled=True)
        with torch.no_grad():
            hist=rollout_history(self.model,head,[10,11,12],7,2,3,3,random.Random(330))
        self.assertLessEqual(len(hist),3)
        self.assertNotIn(3,hist)
    def test_gradients_only_new_head(self):
        for sep in (False,True):
            head=DecoupledHead(16,decoupled=sep)
            loss=training_loss(self.model,head,[10,11],7,2,3,True,random.Random(11))
            loss.backward()
            self.assertTrue(any(p.grad is not None and p.grad.abs().sum()>0 for p in head.parameters()))
        self.assertTrue(all(p.grad is None for p in self.model.parameters()))
    def test_report_eos_partitions(self):
        head=DecoupledHead(16,decoupled=True).eval()
        result=evaluate(self.model,head,[[10,11],[11,10]],7,2,3)
        self.assertEqual(result["total"],2)
        self.assertEqual(sum(result["eos"].values()),2)
if __name__=="__main__":unittest.main()
