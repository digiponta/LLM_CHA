"""v0.13.34 isolated RPC dialogue SFT; never modify production model.

Uses dialogue-level prepared splits. Validation is read-only; test is untouched.
"""
import argparse,json,random
from pathlib import Path
import torch
from torch.utils.data import DataLoader
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from online_train import ConversationDataset,masked_loss

def read_rows(path,limit=0):
    if not path.exists():raise FileNotFoundError(path)
    rows=[]
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():continue
            o=json.loads(line)
            if o.get("source")!="rpc-dialogue-sft" or o.get("approval_state")!="UNAPPROVED":
                raise ValueError("unexpected source or approval state")
            if not o.get("user") or not o.get("assistant") or o.get("dialogue_id") is None:
                raise ValueError("invalid RPC pair")
            rows.append(o)
            if limit and len(rows)>=limit:break
    if not rows:raise ValueError(f"empty {path}")
    return rows

def verify_disjoint(train,val,test):
    sets=[{str(r["dialogue_id"]) for r in rows} for rows in (train,val,test)]
    if any(sets[i]&sets[j] for i,j in ((0,1),(0,2),(1,2))):
        raise ValueError("dialogue_id overlap across splits")
    return [len(s) for s in sets]

@torch.no_grad()
def evaluate(model,loader,device):
    model.eval();weighted_sum=0.;total_tokens=0.
    for x,y,mask in loader:
        x=x.to(device);y=y.to(device);mask=mask.to(device)
        tokens=float(mask.sum().item())
        weighted_sum+=float(masked_loss(model,x,y,mask).item())*tokens
        total_tokens+=tokens
    return weighted_sum/max(1.,total_tokens)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data-dir",type=Path,default=Path("results/rpc_sft_full_v01333"))
    p.add_argument("--base",type=Path,default=Path("model/model-gpu-v1.6.2-online.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,default=Path("results/rpc_sft_candidate_v01334.pt"))
    p.add_argument("--report",type=Path,default=Path("results/rpc_sft_train_v01334.json"))
    p.add_argument("--train-limit",type=int,default=1000)
    p.add_argument("--val-limit",type=int,default=200)
    p.add_argument("--test-limit",type=int,default=200)
    p.add_argument("--epochs",type=int,default=2)
    p.add_argument("--batch-size",type=int,default=8)
    p.add_argument("--lr",type=float,default=5e-6)
    p.add_argument("--run",action="store_true")
    a=p.parse_args()
    if min(a.train_limit,a.val_limit,a.test_limit,a.epochs,a.batch_size)<1 or a.lr<=0:
        p.error("limits, epochs, batch and LR must be positive")
    if a.output==a.base:p.error("output cannot overwrite base")
    if a.output.exists() or a.report.exists():p.error("candidate or report already exists")
    splits={key:read_rows(a.data_dir/f"rpc_sft_{key}_v01333.jsonl",getattr(a,key+"_limit"))
            for key in ("train","val","test")}
    distinct=verify_disjoint(splits["train"],splits["val"],splits["test"])
    print(json.dumps({"training_pairs":len(splits["train"]),"validation_pairs":len(splits["val"]),
                      "test_pairs_reserved":len(splits["test"]),"dialogues_per_split":distinct,
                      "run":a.run},ensure_ascii=False,indent=2))
    if not a.run:return
    if not a.base.exists() or not a.tokenizer.exists():p.error("missing base or tokenizer")
    random.seed(42);torch.manual_seed(42)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok=Tokenizer.load(str(a.tokenizer))
    model,_=LanguageModel.load_checkpoint(str(a.base),device=device)
    loaders={}
    for split in ("train","val"):
        pairs=[(r["user"],r["assistant"]) for r in splits[split]]
        ds=ConversationDataset(pairs,tok,model.context_length)
        loaders[split]=DataLoader(ds,batch_size=a.batch_size,shuffle=(split=="train"))
    base_nll=evaluate(model,loaders["val"],device)
    optim=torch.optim.AdamW(model.parameters(),lr=a.lr,weight_decay=.01)
    history=[];best_nll=float("inf");best_state=None;best_epoch=0
    for epoch in range(1,a.epochs+1):
        model.train();running=0.;steps=0
        for x,y,mask in loaders["train"]:
            x=x.to(device);y=y.to(device);mask=mask.to(device)
            optim.zero_grad(set_to_none=True)
            loss=masked_loss(model,x,y,mask)
            loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.0)
            optim.step()
            running+=float(loss.item());steps+=1
        val=evaluate(model,loaders["val"],device)
        history.append({"epoch":epoch,"train_nll":running/max(1,steps),"val_nll":val})
        print(json.dumps(history[-1],ensure_ascii=False))
        if val<best_nll:
            best_nll=val;best_epoch=epoch
            best_state={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
    model.load_state_dict(best_state)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    model.save_checkpoint(str(a.output),epoch=best_epoch,loss=best_nll,
        metadata={"experiment":"RPC_DIALOGUE_SFT_ONLY","approval":"UNAPPROVED",
                  "base":str(a.base),"production_unchanged":True})
    report={"version":"v0.13.34","base_val_nll":base_nll,"best_val_nll":best_nll,
            "best_epoch":best_epoch,"history":history,
            "training_pairs":len(splits["train"]),"validation_pairs":len(splits["val"]),
            "test_pairs_reserved":len(splits["test"]),"production_unchanged":True,
            "heldout_test_evaluated":False}
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
