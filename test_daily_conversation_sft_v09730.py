import unittest
from unittest.mock import patch
import torch
from train_daily_conversation_sft_v09730 import encode_sample,example_loss,PROTECTED
from daily_conversation_foundation_v09728 import dataset,audit

class DummyTokenizer:
    vocab_size=512
    def encode(self,text,add_bos=False,add_eos=False):
        ids=[4+ord(c)%500 for c in text]
        return ([1] if add_bos else [])+ids+([2] if add_eos else [])
class DummyModel(torch.nn.Module):
    context_length=512
    def __init__(self):
        super().__init__()
        self.embedding=torch.nn.Embedding(512,16)
        self.head=torch.nn.Linear(16,512)
    def forward(self,x):return self.head(self.embedding(x))

class SFTTests(unittest.TestCase):
    def test_mask_only_completion(self):
        tok=DummyTokenizer()
        x,y=encode_sample(tok,"満足した","それは良かったね。",512)
        prefix=tok.encode("人: 満足した\nAI: ",add_bos=True)
        self.assertTrue(torch.all(y[:len(prefix)-1]==-100))
        self.assertGreater(int((y!=-100).sum()),0)
    def test_length_guard(self):
        with self.assertRaises(ValueError):
            encode_sample(DummyTokenizer(),"長"*100,"答え",30)
    def test_backward(self):
        model=DummyModel()
        x,y=encode_sample(DummyTokenizer(),"悲しかった","それは悲しかったね。",512)
        loss=example_loss(model,x,y,torch.device("cpu"))
        self.assertTrue(torch.isfinite(loss))
        loss.backward()
        self.assertTrue(any(p.grad is not None for p in model.parameters()))
    def test_protected_qa_and_data_isolation(self):
        d=dataset()
        self.assertEqual(len(PROTECTED),3)
        self.assertEqual(len(d["train"]),30)
        self.assertEqual(len(d["holdout"]),12)
        self.assertTrue(audit(d)["ready_for_controlled_training"])
        self.assertNotIn("思いがけず楽しい一日だった",[x["input"] for x in d["train"]])
if __name__=="__main__": unittest.main()
