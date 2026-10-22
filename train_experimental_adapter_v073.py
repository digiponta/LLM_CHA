"""Train only the experimental adapter on pending Candidate Memory."""
import argparse
import json
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from online_train import ConversationDataset
from candidate_sandbox_train_v072 import select_candidates,digest
from dual_semantic_memory_v071 import DualMemory
from dual_adapters_v073 import DualAdapterModel,frozen_digest,masked_cross_entropy

def run(base_path,tokenizer_path,approved_path,candidate_path,output,rank=8,epochs=3,lr=1e-4):
    output=Path(output).resolve()
    protected=[Path(p).resolve() for p in (base_path,tokenizer_path,approved_path,candidate_path)]
    if output in protected:raise ValueError("output overlaps protected data")
    if output.exists():raise FileExistsError("experimental adapter checkpoint already exists")
    inputs={str(p):digest(p) for p in protected if p.exists()}
    memory=DualMemory(approved_path,candidate_path)
    pending=select_candidates(memory)
    if not pending:raise ValueError("no PENDING knowledge")
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    base,_=LanguageModel.load_checkpoint(str(base_path),device=device)
    tokenizer=Tokenizer.load(str(tokenizer_path))
    if base.vocab_size!=tokenizer.vocab_size:raise ValueError("tokenizer/model vocab mismatch")
    model=DualAdapterModel(base,rank=rank).to(device)
    base_hash=frozen_digest(base)
    trusted_before=model.export_adapter("trusted")
    dataset=ConversationDataset([(r["question"],r["answer"]) for r in pending],tokenizer,base.context_length)
    optimizer=torch.optim.AdamW(model.training_parameters("experimental"),lr=lr)
    losses=[]
    for epoch in range(epochs):
        model.train()
        for i in range(len(dataset)):
            x,y,mask=(v.unsqueeze(0).to(device) for v in dataset[i])
            optimizer.zero_grad(set_to_none=True)
            loss=masked_cross_entropy(model(x,route="experimental"),y,mask)
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach().item()))
    if frozen_digest(base)!=base_hash:raise RuntimeError("base weights modified")
    if any(not torch.equal(v,model.export_adapter("trusted")[k]) for k,v in trusted_before.items()):
        raise RuntimeError("trusted adapter unexpectedly changed")
    if any(not p.exists() or digest(p)!=h for p,h in ((Path(k),v) for k,v in inputs.items())):
        raise RuntimeError("protected input changed")
    output.parent.mkdir(parents=True,exist_ok=True)
    torch.save({"format":"llm-cha-experimental-adapter-v0.7.3",
       "route":"experimental","rank":rank,"base_hash":base_hash,
       "adapter":model.export_adapter("experimental"),"candidate_ids":[r["id"] for r in pending],
       "source_ids":[r["source_id"] for r in pending],"losses":losses,
       "approved":False,"trusted_deployable":False,"auto_promote":False},output)
    return {"pass":True,"device":str(device),"candidate_count":len(pending),
        "steps":len(losses),"first_loss":losses[0],"last_loss":losses[-1],
        "base_unchanged":True,"trusted_adapter_unchanged":True,"checkpoint":str(output)}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    ap.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    ap.add_argument("--approved",default="data/approved_v071.jsonl")
    ap.add_argument("--candidates",default="data/candidates_v071.jsonl")
    ap.add_argument("--output",default="results/adapter_sandbox_v073/experimental-adapter.pt")
    ap.add_argument("--rank",type=int,default=8)
    ap.add_argument("--epochs",type=int,default=3)
    ap.add_argument("--learning-rate",type=float,default=1e-4)
    args=ap.parse_args()
    result=run(args.base,args.tokenizer,args.approved,args.candidates,args.output,
               rank=args.rank,epochs=args.epochs,lr=args.learning_rate)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
