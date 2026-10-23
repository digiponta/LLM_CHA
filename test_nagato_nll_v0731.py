import unittest
import torch
from diagnose_nagato_nll_v0731 import diagnose

class FakeTokenizer:
    pad_id=0
    eos_id=2
    def encode(self,text,add_bos=False,add_eos=False):
        tokens=[3+(ord(c)%30) for c in text]
        if add_bos:tokens=[1]+tokens
        if add_eos:tokens=tokens+[2]
        return tokens

class FakeBase(torch.nn.Module):
    context_length=128
    def forward(self,x):
        logits=torch.zeros(x.size(0),x.size(1),64)
        return logits

class FakeModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.base=FakeBase()
    def forward(self,x,route="experimental"):
        return self.base(x)

class NagatoNllTests(unittest.TestCase):
    def test_metric_shape(self):
        rows=[{"id":"c1","source_id":"test","question":"Q","answer":"A"}]
        r=diagnose(FakeModel(),FakeTokenizer(),rows,torch.device("cpu"),5)
        self.assertEqual(r["count"],1)
        self.assertAlmostEqual(r["base_mean_nll"],r["experimental_mean_nll"])
        self.assertEqual(r["first_top1_base"],1)
        self.assertEqual(r["first_topk_experimental"],1)
        self.assertEqual(r["cases"][0]["supervised_tokens"],2)
    def test_multiple(self):
        rows=[{"id":str(i),"source_id":"s","question":"Q","answer":"A"+str(i)} for i in range(2)]
        r=diagnose(FakeModel(),FakeTokenizer(),rows,torch.device("cpu"),5)
        self.assertEqual(r["count"],2)
if __name__=="__main__":unittest.main()
