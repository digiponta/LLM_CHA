"""v0.7.3 frozen-base residual low-rank adapters.

This is an experimental bottleneck adapter at the hidden-state output,
not standard attention-layer LoRA. The two adapters never share parameters.
"""
import hashlib
import torch
from torch import nn
from torch.nn import functional as F

class ResidualAdapter(nn.Module):
    def __init__(self,d_model,rank=8,scale=1.0):
        super().__init__()
        self.down=nn.Linear(d_model,rank,bias=False)
        self.up=nn.Linear(rank,d_model,bias=False)
        self.scale=float(scale)
        nn.init.normal_(self.down.weight,std=0.02)
        nn.init.zeros_(self.up.weight)
    def forward(self,hidden):
        return hidden+self.scale*self.up(self.down(hidden))

class DualAdapterModel(nn.Module):
    def __init__(self,base,rank=8):
        super().__init__()
        self.base=base
        for p in self.base.parameters():
            p.requires_grad_(False)
        self.base.eval()
        self.trusted=ResidualAdapter(base.d_model,rank)
        self.experimental=ResidualAdapter(base.d_model,rank)
    def train(self,mode=True):
        super().train(mode)
        self.base.eval()
        return self
    def forward(self,ids,route="experimental"):
        if route not in ("trusted","experimental"):
            raise ValueError("invalid adapter route")
        with torch.no_grad():
            hidden=self.base.forward_hidden(ids)
        adapter=self.trusted if route=="trusted" else self.experimental
        return self.base.lm_head(adapter(hidden))
    def training_parameters(self,route):
        if route not in ("trusted","experimental"):raise ValueError("invalid adapter route")
        return list((self.trusted if route=="trusted" else self.experimental).parameters())
    def export_adapter(self,route):
        target=self.trusted if route=="trusted" else self.experimental
        if route not in ("trusted","experimental"):raise ValueError("invalid adapter route")
        return {k:v.detach().cpu().clone() for k,v in target.state_dict().items()}

def frozen_digest(base):
    digest=hashlib.sha256()
    for name,value in sorted(base.state_dict().items()):
        digest.update(name.encode())
        digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()

def masked_cross_entropy(logits,y,mask):
    loss=F.cross_entropy(logits.reshape(-1,logits.shape[-1]),y.reshape(-1),reduction="none").view_as(y)
    return (loss*mask).sum()/mask.sum().clamp_min(1.0)
