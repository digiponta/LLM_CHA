import unittest
from unittest.mock import patch
import torch
from semantic_decode_v0101 import decode

class Tok:
    eos_id=3
    def encode(self,prompt,add_bos=False):return [0]
    def decode(self,ids,skip_special_tokens=True):
        return "".join({1:"a",2:"\\n",3:""}.get(i,"?") for i in ids)

class Model:
    context_length=16
    def __init__(self,which):self.which=which;self.p=torch.nn.Parameter(torch.zeros(1))
    def parameters(self):return iter([self.p])
    def eval(self):return self
    def __call__(self,x):
        # One-step most likely token determines termination.
        scores=torch.tensor([[-20.,-10.,-10.,-10.]],dtype=torch.float32)
        scores[0,self.which]=20.
        return scores.view(1,1,-1)

class Tests(unittest.TestCase):
    def test_eos(self):
        self.assertEqual(decode(Model(3),Tok(),"q").termination_reason,"EOS")
    def test_newline(self):
        self.assertEqual(decode(Model(2),Tok(),"q").termination_reason,"NEWLINE")
    def test_cap(self):
        r=decode(Model(1),Tok(),"q",max_new_tokens=2)
        self.assertEqual(r.termination_reason,"MAX_TOKENS")
        self.assertEqual(r.text,"aa")
if __name__=="__main__":unittest.main()
