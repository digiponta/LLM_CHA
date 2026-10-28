import unittest
import torch
from sweep_offline_decoding_v0135814 import SETTINGS,adjusted_logits,choose,decode_steps

class ToyTokenizer:
    eos_id=3
    def encode(self,s,add_bos=True):return [1,2]
    def decode(self,ids,skip_special_tokens=True):return "".join(str(x) for x in ids)
class Toy(torch.nn.Module):
    context_length=16
    def __init__(self):
        super().__init__()
        self.p=torch.nn.Parameter(torch.tensor(0.))
    def forward(self,x):
        out=torch.zeros((1,x.shape[1],5),device=x.device)
        out[:,:,-1]=4.
        return out
class Tests(unittest.TestCase):
    def test_modes(self):
        self.assertEqual(len(SETTINGS),5)
        self.assertEqual(SETTINGS["greedy"]["temperature"],0.)
    def test_greedy(self):
        self.assertEqual(choose(torch.tensor([0.,1.,4.]),0.,None),2)
    def test_penalty(self):
        r=adjusted_logits(torch.tensor([2.,-2.,0.]),[0,1],2.)
        self.assertEqual(r.tolist(),[1.,-4.,0.])
    def test_trace_probability(self):
        m=Toy()
        r=decode_steps(m,ToyTokenizer(),"a",SETTINGS["greedy"],7,max_new_tokens=3,trace_steps=2)
        self.assertEqual(r["generated_tokens"],3)
        self.assertEqual(r["trace"][0]["chosen_id"],4)
        self.assertEqual(len(r["trace"][0]["top5"]),5)
        self.assertTrue(0<r["trace"][0]["chosen_probability"]<=1)
    def test_seed_reproducible(self):
        m=Toy();tok=ToyTokenizer()
        a=decode_steps(m,tok,"x",SETTINGS["topk5"],19,max_new_tokens=5)
        b=decode_steps(m,tok,"x",SETTINGS["topk5"],19,max_new_tokens=5)
        self.assertEqual(a,b)
    def test_invalid_steps(self):
        with self.assertRaises(ValueError):
            decode_steps(Toy(),ToyTokenizer(),"x",SETTINGS["greedy"],1,max_new_tokens=0)
if __name__=="__main__":unittest.main()
