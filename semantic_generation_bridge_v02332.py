"""v0.2.33.2 experimental Semantic-to-Generation Bridge.

Frozen checkpoint + trained additive last-hidden projection. Teacher semantic
labels are supplied externally: this is NOT DSS-free internalization.
"""
import argparse,hashlib,json,random
from pathlib import Path
import torch
from torch import nn
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from semantic_memory_expansion_v02328 import load_rows
from train_purpose_sft_v02324 import encode_row
from evaluate_semantic_transfer_v02327 import PROBES,prompt_for

DIM=64
def semantic_vector(topic,purposes,relation="",dim=DIM):
    """Deterministic signed hashed features; NOT an LLM_SEM embedding."""
    v=torch.zeros(dim)
    for part in [f"topic:{topic}",*(f"purpose:{p}" for p in purposes),f"relation:{relation}"]:
        if not part or part.endswith(":"):continue
        h=hashlib.sha256(part.encode("utf-8")).digest()
        index=int.from_bytes(h[:4],"big")%dim
        sign=1. if (h[4]&1) else -1.
        v[index]+=sign
    return F.normalize(v,dim=0) if float(v.norm())>0 else v

def features(row):
    c=row["canonical"]
    return semantic_vector(c.get("topic") or "",c.get("purposes") or [],c.get("relation") or "")

class Bridge(nn.Module):
    def __init__(self,hidden_size,dim=DIM):
        super().__init__()
        self.projector=nn.Linear(dim,hidden_size,bias=False)
        nn.init.zeros_(self.projector.weight)
    def forward(self,hidden,semantics):
        return hidden+self.projector(semantics).unsqueeze(1)

def bridge_logits(model,bridge,x,semantic):
    hidden=model.forward_hidden(x)
    return model.lm_head(bridge(hidden,semantic))

def load_train(path):
    rows=[r for r in load_rows(path) if r["review_status"]=="APPROVED"]
    if not rows:raise ValueError("No approved Semantic Memory expansion")
    return rows

def fit(base,tokenizer,rows,output,epochs,lr,device,seed):
    torch.manual_seed(seed);random.seed(seed)
    model,_=LanguageModel.load_checkpoint(base,device)
    if model.vocab_size!=tokenizer.vocab_size:raise ValueError("Vocabulary mismatch")
    model.eval()
    for p in model.parameters():p.requires_grad_(False)
    bridge=Bridge(model.d_model).to(device)
    pairs=[]
    for row in rows:
        x,y=encode_row(tokenizer,row,model.context_length)
        pairs.append((x.to(device),y.to(device),features(row).to(device)))
    optimizer=torch.optim.AdamW(bridge.parameters(),lr=lr,weight_decay=0.)
    trace=[]
    for epoch in range(epochs):
        order=list(range(len(pairs)));random.shuffle(order)
        total=0.
        for i in order:
            x,y,s=pairs[i]
            optimizer.zero_grad(set_to_none=True)
            logits=bridge_logits(model,bridge,x.unsqueeze(0),s.unsqueeze(0))
            loss=F.cross_entropy(logits.reshape(-1,model.vocab_size),y,ignore_index=-100)
            loss.backward()
            optimizer.step()
            total+=loss.item()
        value=total/len(pairs);trace.append(value)
        print(f"bridge epoch={epoch+1:02d} train_nll={value:.4f}")
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    torch.save({"version":"v0.2.33.2","bridge_state_dict":bridge.state_dict(),
                "hidden_size":model.d_model,"semantic_dim":DIM,"base":base,
                "epochs":epochs,"train_nll":trace[-1]},output)
    return trace

@torch.inference_mode()
def generate(model,tok,bridge,prompt,semantic,max_new_tokens=64):
    ids=tok.encode(prompt,add_bos=True)
    prompt_size=len(ids)
    device=next(model.parameters()).device
    semantic=semantic.to(device).view(1,-1)
    for _ in range(max_new_tokens):
        context=ids[-model.context_length:]
        x=torch.tensor([context],dtype=torch.long,device=device)
        logits=bridge_logits(model,bridge,x,semantic)[0,-1]
        next_id=int(logits.argmax().item())
        ids.append(next_id)
        if next_id==tok.eos_id:break
    return tok.decode(ids[prompt_size:]).split("\n人:",1)[0].split("\nAI:",1)[0].strip()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("train","evaluate"))
    p.add_argument("--expansion",default="data/semantic_expansion_v02328.jsonl")
    p.add_argument("--base",default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--bridge",default="model/semantic-bridge-v02332.pt")
    p.add_argument("--out",default="results/semantic_bridge_eval_v02332.json")
    p.add_argument("--epochs",type=int,default=12)
    p.add_argument("--lr",type=float,default=.005)
    p.add_argument("--max-new-tokens",type=int,default=64)
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--seed",type=int,default=42)
    a=p.parse_args()
    device=torch.device("cuda" if a.device=="auto" and torch.cuda.is_available() else "cpu" if a.device=="auto" else a.device)
    tok=Tokenizer.load(a.tokenizer)
    if a.command=="train":
        if not 1<=a.epochs<=10000 or a.lr<=0:raise ValueError("Invalid training parameters")
        if Path(a.bridge).exists():raise FileExistsError(a.bridge)
        fit(a.base,tok,load_train(a.expansion),a.bridge,a.epochs,a.lr,device,a.seed)
        print("Saved:",a.bridge)
        return
    model,_=LanguageModel.load_checkpoint(a.base,device)
    model.eval()
    checkpoint=torch.load(a.bridge,map_location=device,weights_only=True)
    if checkpoint["hidden_size"]!=model.d_model or checkpoint["semantic_dim"]!=DIM:
        raise ValueError("Incompatible bridge")
    bridge=Bridge(model.d_model).to(device)
    bridge.load_state_dict(checkpoint["bridge_state_dict"]);bridge.eval()
    result=[]
    for probe in PROBES:
        purpose=probe["purpose"].split(",")
        semantic=semantic_vector(probe["topic"],purpose).to(device)
        short=prompt_for(probe)
        raw=f"人: {probe['user']}\nAI: "
        modes={}
        for mode,prompt in (("raw",raw),("short",short)):
            modes[mode]={
                "zero_semantic":generate(model,tok,bridge,prompt,torch.zeros(DIM,device=device),a.max_new_tokens),
                "teacher_semantic":generate(model,tok,bridge,prompt,semantic,a.max_new_tokens)}
        result.append({"user":probe["user"],"purpose":purpose,"modes":modes})
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps({"results":result,"promotion_eligible":False},ensure_ascii=False,indent=2),encoding="utf-8")
    for r in result:
        print(r["user"])
        for mode,variants in r["modes"].items():print(" ",mode,variants)
    print("Saved:",dest)
if __name__=="__main__":main()
