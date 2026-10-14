"""v0.4.28.29: tiny trainable QA pair cross-encoder (weak-label demonstration).

All 64 records are DEVELOPMENT ONLY. In-sample predictions are NOT evaluation.
No Truth Gate integration or remote model downloads.
"""
import argparse,hashlib,json,math,random
from pathlib import Path
from semantic_qa_model_contract_v042828 import design,validate_predictions

def encode_pair(question,answer,limit=160,vocab=4096):
    # Shared hash embedding; segment embeddings distinguish question and answer.
    q=[3+(ord(c)% (vocab-3)) for c in question[:(limit-3)//2]]
    a=[3+(ord(c)% (vocab-3)) for c in answer[:(limit-3)//2]]
    tokens=[1]+q+[2]+a
    segments=[0]*(len(q)+2)+[1]*len(a)
    return tokens,segments

def fit_predict(contract,epochs=30,seed=20261014,device="cpu"):
    import torch
    from torch import nn
    torch.manual_seed(seed);random.seed(seed)
    torch.set_num_threads(min(torch.get_num_threads(),4))
    cases=contract["cases"]
    labeled=[r for r in cases if r["provisional_chatgpt_label"] is not None]
    if len(cases)!=64 or len(labeled)<2 or len(set(r["provisional_chatgpt_label"] for r in labeled))!=2:
        raise ValueError("requires 64 cases with both provisional classes")
    class TinyCrossEncoder(nn.Module):
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
            # Masked mean over tokens avoids pooling on padded positions.
            pooled=(h*mask.unsqueeze(-1)).sum(1)/mask.sum(1).clamp(min=1).unsqueeze(-1)
            return self.head(pooled).squeeze(-1)
    model=TinyCrossEncoder().to(device)
    def batch(items):
        enc=[encode_pair(r["question"],r["answer"]) for r in items]
        width=max(len(t) for t,s in enc)
        ids=torch.zeros(len(enc),width,dtype=torch.long,device=device)
        seg=torch.zeros_like(ids);mask=torch.zeros_like(ids,dtype=torch.bool)
        for i,(t,s) in enumerate(enc):
            ids[i,:len(t)]=torch.tensor(t,device=device)
            seg[i,:len(s)]=torch.tensor(s,device=device)
            mask[i,:len(t)]=True
        return ids,seg,mask
    opt=torch.optim.AdamW(model.parameters(),lr=0.001)
    weights=torch.tensor([1.0, max(1.0,sum(r["provisional_chatgpt_label"] is False for r in labeled)/max(1,sum(r["provisional_chatgpt_label"] is True for r in labeled)))],device=device)
    last_loss=None
    for epoch in range(epochs):
        model.train()
        order=list(range(len(labeled)));random.shuffle(order)
        total=0.0
        for start in range(0,len(order),16):
            rows=[labeled[k] for k in order[start:start+16]]
            ids,seg,mask=batch(rows)
            target=torch.tensor([float(r["provisional_chatgpt_label"]) for r in rows],device=device)
            logits=model(ids,seg,mask)
            loss=nn.functional.binary_cross_entropy_with_logits(logits,target,pos_weight=weights[1])
            opt.zero_grad();loss.backward();nn.utils.clip_grad_norm_(model.parameters(),1.0);opt.step()
            total+=loss.item()*len(rows)
        last_loss=total/len(labeled)
    model.eval();predictions=[]
    with torch.no_grad():
        for row in cases:
            ids,seg,mask=batch([row])
            score=float(torch.sigmoid(model(ids,seg,mask))[0].item())
            # No calibrated cutoff has been established: abstain rather than infer relevance.
            predictions.append({"id":row["id"],"turn":row["turn"],
              "decision":"ABSTAIN","score":None,"diagnostic_uncalibrated_probability":round(score,6)})
    packet={"schema":"llm_cha_semantic_qa_predictions_v1","method":"cross_encoder",
      "dataset_split":"DEVELOPMENT_ONLY","predictions":[
      {k:r[k] for k in ("id","turn","decision","score")} for r in predictions]}
    validated=validate_predictions(contract,packet)
    return {"version":"v0.4.28.29","mode":"WEAK_LABEL_IN_SAMPLE_DEMONSTRATION",
      "model":"2_layer_64_dim_transformer_char_hash_cross_encoder",
      "architecture_not_pretrained":True,"trained_on_development_labels":True,
      "no_independent_evaluation":True,"labels_are_chatgpt_provisional":True,
      "model_score_calibrated":False,"runtime_modified":False,"seed":seed,
      "epochs":epochs,"training_examples":len(labeled),"in_sample_training_loss":round(last_loss,6),
      "predictions":predictions,"protocol":validated}

def main():
    p=argparse.ArgumentParser()
    for arg in ("validation","labels","output"):p.add_argument("--"+arg,required=True)
    p.add_argument("--epochs",type=int,default=30)
    p.add_argument("--device",choices=["cpu","cuda"],default="cpu")
    a=p.parse_args()
    try:
        if not 1<=a.epochs<=100:raise ValueError("epochs must be 1..100")
        paths=[Path(a.validation),Path(a.labels)]
        dst=Path(a.output)
        if any(not f.is_file() or f.is_symlink() for f in paths) or dst.exists() or dst.is_symlink():raise ValueError("invalid paths")
        v,l=[json.loads(f.read_text(encoding="utf-8-sig")) for f in paths]
        contract=design(v,l)
        result=fit_predict(contract,a.epochs,device=a.device)
        result["sha256"]={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in paths}
        dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({k:result[k] for k in ("mode","training_examples","epochs","in_sample_training_loss")}))
    except (OSError,ValueError,ImportError,RuntimeError,KeyError,TypeError) as e:p.exit(1,f"Cross-Encoder experiment failed: {e}\n")
if __name__=="__main__":main()
