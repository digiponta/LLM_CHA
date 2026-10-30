import json
import tempfile
import unittest
from pathlib import Path
import torch
from train_negative_only_v013588247 import read_negative_signals, unlikelihood_loss

class NegativeOnlyExperimentTests(unittest.TestCase):
 def test_only_untrained_negative_records(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"signals.jsonl"
   rows=[
    {"signal":"NEGATIVE","training_status":"NOT_TRAINED","question":"宇宙","rejected_answer":"1967年 APB"},
    {"signal":"NEGATIVE","training_status":"NOT_TRAINED","question":"宇宙","rejected_answer":"1967年 APB"},
    {"signal":"NEGATIVE","training_status":"TRAINED","question":"CPU","rejected_answer":"wrong"},
    {"signal":"POSITIVE","training_status":"NOT_TRAINED","question":"GPU","rejected_answer":"wrong"}]
   p.write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in rows),encoding="utf-8")
   self.assertEqual(len(read_negative_signals(p)),1)
 def test_no_signals(self):
  with tempfile.TemporaryDirectory() as td:
   self.assertEqual(read_negative_signals(Path(td)/"absent.jsonl"),[])
 def test_negative_gradient_reduces_bad_probability(self):
  class Tiny(torch.nn.Module):
   def __init__(self):
    super().__init__()
    self.logits=torch.nn.Parameter(torch.tensor([0.0,0.0]))
   def forward(self,x):return self.logits.expand(x.size(0),x.size(1),-1)
  model=Tiny()
  x=torch.zeros((1,2),dtype=torch.long)
  y=torch.zeros((1,2),dtype=torch.long)
  mask=torch.ones((1,2))
  opt=torch.optim.SGD(model.parameters(),lr=0.5)
  before=float(torch.nn.functional.log_softmax(model(x),-1)[0,0,0])
  opt.zero_grad()
  loss=unlikelihood_loss(model,x,y,mask)
  loss.backward()
  opt.step()
  after=float(torch.nn.functional.log_softmax(model(x),-1)[0,0,0])
  self.assertLess(after,before)
if __name__=="__main__":unittest.main()
