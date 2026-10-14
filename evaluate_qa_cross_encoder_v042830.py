"""v0.4.28.30: frozen train/holdout protocol and checkpoint round-trip.

Group by normalized question to prevent exact-question leakage. This is an
INTERNAL development split, NOT an independent external test.
"""
import argparse,hashlib,json,math,random
from pathlib import Path
from train_qa_cross_encoder_v042829 import encode_pair
from semantic_qa_model_contract_v042828 import design

def split_cases(cases,seed=20261014):
    groups={}
    for r in cases:
        q="".join(r["question"].split())
        groups.setdefault(q,[]).append(r)
    keys=sorted(groups)
    rng=random.Random(seed);rng.shuffle(keys)
    target=max(1,round(len(keys)*0.2))
    hold=set(keys[:target])
    train=[r for r in cases if "".join(r["question"].split()) not in hold and type(r["provisional_chatgpt_label"]) is bool]
    test=[r for r in cases if "".join(r["question"].split()) in hold and type(r["provisional_chatgpt_label"]) is bool]
    if not train or not test or len({r["provisional_chatgpt_label"] for r in train})<2:
        raise ValueError("insufficient labeled groups/classes for split")
    return train,test

def run(contract,checkpoint,epochs=15,device="cpu",seed=20261014,split_seed=None,encode_fn=None):
    import torch
    from torch import nn
    if not 1<=epochs<=100:raise ValueError("epochs must be 1..100")
    cases=contract["cases"]
    if len(cases)!=64:raise ValueError("expected development contract of 64 cases")
    train,test=split_cases(cases,seed if split_seed is None else split_seed)
    torch.manual_seed(seed)
    torch.set_num_threads(min(4,torch.get_num_threads()))
    class Encoder(nn.Module):
        def __init__(self):
            super().__init__()
            self.token=nn.Embedding(4096,64,padding_idx=0)
            self.segment=nn.Embedding(2,64)
            self.position=nn.Embedding(160,64)
            layer=nn.TransformerEncoderLayer(64,4,128,dropout=0.0,batch_first=True)
            self.encoder=nn.TransformerEncoder(layer,2,enable_nested_tensor=False)
            self.head=nn.Linear(64,1)
        def forward(self,ids,seg,mask):
            p=torch.arange(ids.shape[1],device=ids.device)[None,:]
            h=self.token(ids)+self.segment(seg)+self.position(p)
            h=self.encoder(h,src_key_padding_mask=~mask)
            pooled=(h*mask.unsqueeze(-1)).sum(1)/mask.sum(1).clamp(min=1).unsqueeze(-1)
            return self.head(pooled).squeeze(-1)
    def tensors(rows):
        pairs=[(encode_pair if encode_fn is None else encode_fn)(r["question"],r["answer"]) for r in rows]
        width=max(len(x[0]) for x in pairs)
        ids=torch.zeros((len(rows),width),dtype=torch.long,device=device)
        seg=torch.zeros_like(ids);mask=torch.zeros_like(ids,dtype=torch.bool)
        for i,(t,s) in enumerate(pairs):
            ids[i,:len(t)]=torch.tensor(t,device=device)
            seg[i,:len(s)]=torch.tensor(s,device=device)
            mask[i,:len(t)]=True
        return ids,seg,mask
    model=Encoder().to(device)
    optimizer=torch.optim.AdamW(model.parameters(),lr=0.001)
    positive=sum(r["provisional_chatgpt_label"] for r in train)
    negative=len(train)-positive
    weight=torch.tensor(max(1.0,negative/positive),device=device)
    rng=random.Random(seed)
    for epoch in range(epochs):
        model.train();order=list(train);rng.shuffle(order)
        for start in range(0,len(order),16):
            items=order[start:start+16]
            logits=model(*tensors(items))
            targets=torch.tensor([float(x["provisional_chatgpt_label"]) for x in items],device=device)
            loss=nn.functional.binary_cross_entropy_with_logits(logits,targets,pos_weight=weight)
            optimizer.zero_grad();loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(),1.0);optimizer.step()
    model.eval()
    with torch.no_grad():
        torch.save({"version":"v0.4.28.30","architecture":"char_hash_transformer_2x64",
          "seed":seed,"epochs":epochs,"state_dict":model.state_dict()},checkpoint)
        # reload checkpoint to confirm round-trip: weights_only=True forbids untrusted pickles.
        stored=torch.load(checkpoint,map_location=device,weights_only=True)
        restored=Encoder().to(device)
        restored.load_state_dict(stored["state_dict"]);restored.eval()
        results=[]
        for split,rows in (("TRAIN",train),("INTERNAL_GROUP_HOLDOUT",test)):
            for item in rows:
                inp=tensors([item])
                first=float(torch.sigmoid(model(*inp)).item())
                again=float(torch.sigmoid(restored(*inp)).item())
                if abs(first-again)>1e-6:raise ValueError("checkpoint round trip mismatch")
                results.append({"id":item["id"],"turn":item["turn"],"split":split,
                  "weak_label":item["provisional_chatgpt_label"],
                  "uncalibrated_score":round(again,6),"decision":"ABSTAIN"})
    return {"version":"v0.4.28.30","mode":"INTERNAL_GROUPED_DEVELOPMENT_EVALUATION",
      "independent_external_holdout":False,"human_ground_truth":False,
      "runtime_modified":False,"automatic_rejection":False,"threshold_fitted":False,
      "checkpoint_verified":True,"train_labeled":len(train),"holdout_labeled":len(test),
      "train_groups":len({"".join(r["question"].split()) for r in train}),
      "holdout_groups":len({"".join(r["question"].split()) for r in test}),
      "epochs":epochs,"records":results}

def main():
    parser=argparse.ArgumentParser()
    for n in ("validation","labels","checkpoint","output"):parser.add_argument("--"+n,required=True)
    parser.add_argument("--epochs",type=int,default=15)
    parser.add_argument("--device",choices=["cpu","cuda"],default="cpu")
    args=parser.parse_args()
    try:
        sources=[Path(args.validation),Path(args.labels)]
        ckpt=Path(args.checkpoint);dest=Path(args.output)
        if any(not p.is_file() or p.is_symlink() for p in sources):
            raise ValueError("source missing or symlink")
        if any(p.exists() or p.is_symlink() for p in (ckpt,dest)):
            raise ValueError("checkpoint/output exists")
        v,l=[json.loads(p.read_text(encoding="utf-8-sig")) for p in sources]
        contract=design(v,l)
        ckpt.parent.mkdir(parents=True,exist_ok=True)
        result=run(contract,ckpt,args.epochs,args.device)
        result["sha256"]={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
        result["checkpoint_sha256"]=hashlib.sha256(ckpt.read_bytes()).hexdigest()
        dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({k:result[k] for k in ("mode","train_labeled","holdout_labeled","train_groups","holdout_groups","checkpoint_verified")}))
    except (OSError,ValueError,RuntimeError,ImportError,KeyError,TypeError) as e:
        parser.exit(1,f"evaluation failed: {e}\n")
if __name__=="__main__":main()
