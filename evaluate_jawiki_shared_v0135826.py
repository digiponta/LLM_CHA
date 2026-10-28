"""v0.13.58.26: four-checkpoint shared Wikipedia validation NLL.

Evaluation only. Same token IDs and masked target positions for every model.
A same-dump article-disjoint split is diagnostic, NOT independent holdout.
No training, auto-approval, checkpoint creation or production promotion.
"""
import argparse,hashlib,json,math
from pathlib import Path

ARMS=("Base","W","WR","WRP")
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def verify(dataset,trained,base,tokenizer,output):
    if output.exists():raise FileExistsError(output)
    manifest=json.loads((dataset/"manifest.json").read_text(encoding="utf-8-sig"))
    if manifest.get("status")!="STAGED_NOT_APPROVED" or manifest.get("validation_scope")!="SAME_DUMP_DIAGNOSTIC_ONLY":
        raise ValueError("invalid dataset status/scope")
    if sha(tokenizer)!=manifest.get("tokenizer_sha256"):raise ValueError("tokenizer hash mismatch")
    val=dataset/"validation_chunks.jsonl";train=dataset/"train_chunks.jsonl"
    for p in (val,train):
        if sha(p)!=manifest.get("file_sha256",{}).get(p.name):raise ValueError("dataset hash mismatch "+p.name)
    train_ids=set()
    with train.open(encoding="utf-8-sig") as f:
        for line in f:
            if line.strip():train_ids.add(str(json.loads(line)["article_id"]))
    rows=[];val_ids=set()
    with val.open(encoding="utf-8-sig") as f:
        for line in f:
            if not line.strip():continue
            item=json.loads(line);ids=item.get("token_ids")
            if not isinstance(ids,list) or not 2<=len(ids)<=513 or any(type(t)!=int or not 0<=t<8000 for t in ids):
                raise ValueError("invalid validation sequence")
            if item.get("supervised_tokens")!=len(ids)-1 or item.get("approval")!="PENDING_REVIEW" or item.get("auto_promote") is not False:
                raise ValueError("invalid validation status")
            val_ids.add(str(item["article_id"]));rows.append(ids)
    if train_ids & val_ids:raise ValueError("train/validation article leak")
    if len(rows)!=manifest["chunks"]["validation"] or sum(len(r)-1 for r in rows)!=manifest["supervised_tokens"]["validation"]:
        raise ValueError("validation counts mismatch")
    paths={"Base":base,**{a:trained/("candidate_"+a+".pt") for a in ARMS[1:]}}
    if any(not p.is_file() for p in paths.values()):raise FileNotFoundError("missing checkpoint")
    # The completed experimental training report binds candidates to original base checkpoint.
    report_path=trained/"report.json"
    report=json.loads(report_path.read_text(encoding="utf-8-sig"))
    if report.get("status")!="EXPLORATORY_TRAINING_COMPLETE" or report.get("checkpoint_sha256")!=sha(base) or report.get("tokenizer_sha256")!=sha(tokenizer):
        raise ValueError("training provenance mismatch")
    for a in ARMS[1:]:
        if sha(paths[a])!=report.get("history",{}).get(a,{}).get("checkpoint_sha256"):
            raise ValueError("candidate hash mismatch "+a)
    return rows,paths,manifest

def compute_nll(model,rows,device,batch_size=4):
    import torch
    import torch.nn.functional as F
    model.eval();numerator=0.;denominator=0
    with torch.inference_mode():
        for begin in range(0,len(rows),batch_size):
            group=rows[begin:begin+batch_size]
            width=max(len(seq)-1 for seq in group)
            x=torch.zeros((len(group),width),dtype=torch.long,device=device)
            y=torch.zeros_like(x);mask=torch.zeros((len(group),width),dtype=torch.float32,device=device)
            for i,seq in enumerate(group):
                n=len(seq)-1
                x[i,:n]=torch.tensor(seq[:-1],dtype=torch.long,device=device)
                y[i,:n]=torch.tensor(seq[1:],dtype=torch.long,device=device)
                mask[i,:n]=1.
            logits=model(x)
            if isinstance(logits,tuple):logits=logits[0]
            per=F.cross_entropy(logits.reshape(-1,logits.size(-1)),y.reshape(-1),reduction="none").reshape_as(y)
            numerator+=float((per*mask).sum().item())
            denominator+=int(mask.sum().item())
    if denominator==0:raise ValueError("no supervised tokens")
    nll=numerator/denominator
    return {"nll":nll,"perplexity":math.exp(nll),"supervised_tokens":denominator,"chunks":len(rows)}

def evaluate(dataset,trained,base,tokenizer,output,batch_size=4,device_choice="auto",dry_run=False):
    if batch_size<1:raise ValueError("invalid batch size")
    rows,paths,m=verify(dataset,trained,base,tokenizer,output)
    result={"version":"v0.13.58.26","status":"EVAL_PREFLIGHT" if dry_run else "DIAGNOSTIC_EVALUATION_COMPLETE",
        "validation_scope":"SAME_DUMP_DIAGNOSTIC_ONLY","validation_chunks":len(rows),
        "validation_supervised_tokens":sum(len(r)-1 for r in rows),
        "dataset_manifest_sha256":sha(dataset/"manifest.json"),
        "checkpoint_sha256":{arm:sha(p) for arm,p in paths.items()},
        "tokenizer_sha256":sha(tokenizer),"models":{},
        "training_performed":False,"independent_holdout_verified":False,
        "human_review_approved":False,"production_promotion_allowed":False}
    if dry_run:return result
    import torch
    from model import LanguageModel
    if device_choice=="auto":device_choice="cuda" if torch.cuda.is_available() else "cpu"
    if device_choice=="cuda" and not torch.cuda.is_available():raise ValueError("CUDA unavailable")
    device=torch.device(device_choice)
    for arm,path in paths.items():
        model,_=LanguageModel.load_checkpoint(str(path),device=device)
        if model.context_length<512 or model.vocab_size!=8000:raise ValueError("checkpoint architecture mismatch: "+arm)
        result["models"][arm]=compute_nll(model,rows,device,batch_size)
        del model
        if torch.cuda.is_available():torch.cuda.empty_cache()
    ref=result["models"]["Base"]["nll"]
    for arm,item in result["models"].items():
        item["nll_delta_vs_base"]=item["nll"]-ref
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--dataset-dir",type=Path,default=Path("results/jawiki_dataset_v0135821"))
    p.add_argument("--trained-dir",type=Path,default=Path("results/jawiki_controlled_v0135825"))
    p.add_argument("--base",type=Path,default=Path("model/model-llm-try-nagato-chat-v94.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,default=Path("results/jawiki_shared_eval_v0135826.json"))
    p.add_argument("--batch-size",type=int,default=4)
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--dry-run",action="store_true")
    a=p.parse_args()
    r=evaluate(a.dataset_dir,a.trained_dir,a.base,a.tokenizer,a.output,a.batch_size,a.device,a.dry_run)
    print(json.dumps(r,ensure_ascii=False,indent=2))
    if not a.dry_run:print("report:",a.output)
if __name__=="__main__":main()
