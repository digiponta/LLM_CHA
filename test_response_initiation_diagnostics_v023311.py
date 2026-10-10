import unittest
from unittest.mock import Mock
import torch
from response_initiation_diagnostics_v023311 import prefix_plan,short_prompt,analyze
class ToyTokenizer:
    eos_id=99
    def encode(self,text,add_bos=False,add_eos=False):
        return ([98] if add_bos else [])+[ord(c)%80 for c in text]+([99] if add_eos else [])
    def decode(self,ids):
        return "".join(chr(i+80) for i in ids if i not in (98,99))
class ToyModel:
    context_length=1024
    def __call__(self,x):
        out=torch.zeros((1,x.shape[1],100))
        out[0,-1,1]=2.0
        return out
    def generate(self,ids,**kwargs):return ids+[1,99]
class InitiationTests(unittest.TestCase):
    def test_prefix_remaining(self):
        t=ToyTokenizer()
        ids,remaining,n=prefix_plan(t,"P","abcd",3)
        self.assertEqual(n,3)
        self.assertEqual(len(remaining),2)
        self.assertEqual(ids[-3:],t.encode("abcd")[:3])
    def test_clamped_prefix(self):
        t=ToyTokenizer()
        _,remaining,n=prefix_plan(t,"P","a",100)
        self.assertEqual(n,1)
        self.assertEqual(remaining,[99])
    def test_prompt_format(self):
        self.assertEqual(short_prompt("猫"),"文章: 猫\n出力: ")
    def test_first_token_rank_and_run(self):
        g=Mock()
        g.tokenizer=ToyTokenizer();g.model=ToyModel();g.device=torch.device("cpu")
        out=analyze(g,"P","ab",0,10)
        self.assertGreaterEqual(out["first_rank"],1)
        self.assertEqual(out["exact_next_token_run"],0)
if __name__=="__main__":unittest.main()
