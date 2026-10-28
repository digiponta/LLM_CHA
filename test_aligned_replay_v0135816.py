import unittest
import torch
from aligned_replay_examples_v0135816 import split_dialogue,make_aligned_examples
from audit_offline_replay_v0135810 import read_file
from pathlib import Path
import tempfile,json

class ToyTokenizer:
 pad_id=0;eos_id=3
 def encode(self,s,add_bos=False,add_eos=False):
  r=([1] if add_bos else [])+[10+(ord(ch)%60) for ch in s]
  return r+([3] if add_eos else [])
class Tests(unittest.TestCase):
 def test_canonical_jsonl(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"sample.jsonl"
   p.write_text(json.dumps({"approved":True,"user":"こんにちは","assistant":"こんにちは。"},ensure_ascii=False)+"\n",encoding="utf-8")
   self.assertEqual(read_file(p),["人: こんにちは\nAI: こんにちは。"])
 def test_split(self):
  self.assertEqual(split_dialogue("人: 質問\nAI: 回答"),("人: 質問\nAI: ","回答"))
 def test_reject_mismatched(self):
  with self.assertRaises(ValueError):split_dialogue("人: 質問 AI: 回答")
 def test_assistant_mask(self):
  tok=ToyTokenizer();line="人: 質問\nAI: 回答"
  prompt,_=split_dialogue(line)
  prefix=tok.encode(prompt,add_bos=True)
  ds=make_aligned_examples([("conversation",line)],tok,128)
  x,y,mask=ds[0]
  self.assertEqual(float(mask[:len(prefix)-1].sum()),0.)
  self.assertEqual(int(mask.sum().item()),len(tok.encode("回答",add_eos=True)))
  self.assertEqual(int(y[len(prefix)-1]),tok.encode("回答")[0])
 def test_literature_full_loss(self):
  ds=make_aligned_examples([("literature","吾輩は猫である。")],ToyTokenizer(),128)
  self.assertGreater(float(ds[0][2].sum()),0.)
 def test_full_loss_ablation(self):
  line="人: 質問\nAI: 回答"
  d1=make_aligned_examples([("conversation",line)],ToyTokenizer(),128,assistant_only=True)
  d2=make_aligned_examples([("conversation",line)],ToyTokenizer(),128,assistant_only=False)
  self.assertGreater(float(d2[0][2].sum()),float(d1[0][2].sum()))
 def test_long_context_chunking(self):
  ds=make_aligned_examples([("conversation","人: "+"長"*40+"\nAI: "+"回答"*20)],ToyTokenizer(),16)
  self.assertGreater(len(ds),1)
if __name__=="__main__":unittest.main()
