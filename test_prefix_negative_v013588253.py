import unittest
from unittest.mock import patch
import torch
from train_prefix_negative_v013588253 import step_loss

class TinyModel(torch.nn.Module):
 def __init__(self):
  super().__init__()
  self.logits=torch.nn.Parameter(torch.tensor([0.0,0.0]))
 def forward(self,x):
  return self.logits.expand(x.shape[0],x.shape[1],-1)

class PrefixNegativeTests(unittest.TestCase):
 def test_uniform_matches_no_prefix(self):
  m=TinyModel()
  ref=TinyModel()
  encoded=([[1],[1,0]],[0,1])
  a=step_loss(m,ref,encoded,0.05,1.0,0,1.0)
  b=step_loss(m,ref,encoded,0.05,1.0,8,1.0)
  self.assertAlmostEqual(float(a),float(b),places=6)
 def test_prefix_bias_changes_loss_when_positions_differ(self):
  class PositionModel(torch.nn.Module):
   def __init__(self):
    super().__init__()
    self.weight=torch.nn.Parameter(torch.tensor(1.5))
   def forward(self,x):
    v=self.weight*x.float().sum(dim=1,keepdim=True)
    return torch.stack([v,-v],dim=-1).expand(-1,x.shape[1],-1)
  m=PositionModel()
  ref=PositionModel()
  encoded=([[1],[1,0]],[0,1])
  ordinary=step_loss(m,ref,encoded,1.0,0.0,0,1.0)
  biased=step_loss(m,ref,encoded,1.0,0.0,1,8.0)
  self.assertNotAlmostEqual(float(ordinary),float(biased),places=5)
if __name__=="__main__": unittest.main()
