"""v0.7.25 non-mutating Experimental /sleep impact and protection audit."""
import argparse
import hashlib
import json
from pathlib import Path

def sha256(path):
    p=Path(path)
    if not p.exists():return None
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def evaluate_rows(model,tokenizer,rows,*,max_tokens=32):
    from dual_inference_v075 import generate
    cases=[]
    for row in rows:
        base=generate(model,tokenizer,row["question"],"base",max_tokens)
        experimental=generate(model,tokenizer,row["question"],"experimental",max_tokens)
        cases.append({"question":row["question"],"reference":row["answer"],
                      "base_output":base,"experimental_output":experimental,
                      "base_exact":base==row["answer"],
                      "experimental_exact":experimental==row["answer"]})
    return {"count":len(cases),"base_exact":sum(x["base_exact"] for x in cases),
            "experimental_exact":sum(x["experimental_exact"] for x in cases),
            "cases":cases}

def audit(base_path,tokenizer_path,approved_path,candidates_path,adapter_path,
          output_path,holdouts_path=None,max_tokens=32):
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    from dual_adapters_v073 import DualAdapterModel
    from evaluate_dual_adapter_v074 import load_experimental
    from dual_semantic_memory_v071 import DualMemory
    if not 1<=max_tokens<=128:raise ValueError("max_tokens must be 1..128")
    paths=[Path(p).resolve() for p in
           (base_path,tokenizer_path,approved_path,candidates_path,adapter_path)]
    if holdouts_path:paths.append(Path(holdouts_path).resolve())
    if Path(output_path).resolve() in paths:raise ValueError("output overlaps protected input")
    pre={str(p):sha256(p) for p in paths}
    missing=[str(p) for p in paths if not p.exists()]
    if missing:raise FileNotFoundError(", ".join(missing))
    memory=DualMemory(approved_path,candidates_path)
    pending=[r for r in memory.candidates() if r["status"]=="PENDING"]
    if not pending:raise ValueError("no PENDING candidates")
    approved=memory.approved()
    holdouts=[]
    if holdouts_path:
        data=json.loads(Path(holdouts_path).read_text(encoding="utf-8"))
        if not isinstance(data,list):raise ValueError("holdouts must be array")
        candidates_by_id={r["id"]:r for r in pending}
        trained_questions={r["question"].strip() for r in pending}
        for x in data:
            if not isinstance(x,dict) or not isinstance(x.get("question"),str):
                raise ValueError("bad holdout")
            if x["question"].strip() in trained_questions:
                raise ValueError("holdout includes training question")
            matching=candidates_by_id.get(x.get("candidate_id"))
            if matching is None or x.get("reference")!=matching["answer"]:
                raise ValueError("holdout does not match current PENDING candidate")
            holdouts.append({"question":x["question"],"answer":x["reference"]})
    saved=torch.load(adapter_path,map_location="cpu",weights_only=True)
    if saved.get("route")!="experimental" or saved.get("approved") is not False:
        raise ValueError("not an Experimental checkpoint")
    ids=[r["id"] for r in pending]
    if set(saved.get("candidate_ids",[]))!=set(ids):
        raise ValueError("checkpoint candidate snapshot mismatch")
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    base,_=LanguageModel.load_checkpoint(str(base_path),device=device)
    tokenizer=Tokenizer.load(str(tokenizer_path))
    if base.vocab_size!=tokenizer.vocab_size:raise ValueError("tokenizer mismatch")
    model=DualAdapterModel(base,rank=int(saved["rank"])).to(device)
    load_experimental(model,adapter_path)
    train=evaluate_rows(model,tokenizer,pending,max_tokens=max_tokens)
    hold=evaluate_rows(model,tokenizer,holdouts,max_tokens=max_tokens)
    approved_eval=evaluate_rows(model,tokenizer,approved,max_tokens=max_tokens)
    post={str(p):sha256(p) for p in paths}
    unchanged=pre==post
    report={"version":"v0.7.25","device":str(device),
      "comparison":"same frozen Base versus Experimental Adapter after sleep; before-training inference was NOT recorded",
      "training":train,"holdout":hold,"approved_probe":approved_eval,
      "approved_probe_available":bool(approved),
      "protected_file_hashes_before":pre,"protected_file_hashes_after":post,
      "protected_files_unchanged":unchanged,
      "trusted_weights_unchanged_by_audit":pre[str(Path(base_path).resolve())]==post[str(Path(base_path).resolve())],
      "experimental_checkpoint":str(adapter_path),"auto_promote":False,
      "factual_verification":"NOT_PERFORMED"}
    if not unchanged:raise RuntimeError("protected experiment inputs changed during audit")
    out=Path(output_path)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--approved",default="data/approved_v071.jsonl")
    p.add_argument("--candidates",default="data/candidates_v071.jsonl")
    p.add_argument("--adapter",required=True)
    p.add_argument("--holdouts")
    p.add_argument("--max-tokens",type=int,default=32)
    p.add_argument("--output",default="results/experimental_audit_v0725/report.json")
    a=p.parse_args()
    report=audit(a.base,a.tokenizer,a.approved,a.candidates,a.adapter,
                 a.output,a.holdouts,a.max_tokens)
    print(json.dumps({"version":report["version"],"device":report["device"],
        "train_base_exact":report["training"]["base_exact"],
        "train_experimental_exact":report["training"]["experimental_exact"],
        "holdout_count":report["holdout"]["count"],
        "holdout_experimental_exact":report["holdout"]["experimental_exact"],
        "approved_count":report["approved_probe"]["count"],
        "protected_files_unchanged":report["protected_files_unchanged"],
        "auto_promote":False},ensure_ascii=False,indent=2))
    print("report:",a.output)
if __name__=="__main__":main()
