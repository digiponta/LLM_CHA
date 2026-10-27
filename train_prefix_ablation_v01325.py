"""v0.13.25 controlled answer-prefix ablation on the same base checkpoint.

A: original annotation in target; B/C: raw text, approval external;
D: natural introduction plus raw text. B and C share identical weights.
Dry run by default. --run trains isolated candidates; no promotion.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from unapproved_corpus_learning_v0139 import load_jsonl
from online_train import pair_fingerprint

LABELS=("【未承認の記録・事実未検証】","【未承認の記録】","【未承認・事実未検証の原文】")
VARIANTS=("A_LABEL","B_RAW","D_NATURAL")
def strip_label(text):
    for label in LABELS:
        if text.startswith(label):
            return text[len(label):].strip()
    return re.sub(r"^【[^】]{1,40}】","",text).strip()

def transform(row,variant):
    text=strip_label(str(row["assistant"]))
    if not text:raise ValueError("empty source text")
    if variant=="A_LABEL":answer="【未承認の記録・事実未検証】"+text
    elif variant=="B_RAW":answer=text
    elif variant=="D_NATURAL":answer="原文では、"+text
    else:raise ValueError("unknown variant")
    return {"user":row["user"],"assistant":answer,"source":"corpus-unapproved",
            "knowledge_id":row["knowledge_id"],"subject":row.get("subject",""),
            "approval_state":"UNAPPROVED","truth_state":"UNVERIFIED",
            "pair_fingerprint":pair_fingerprint(row["user"],answer)}

def prepare(rows,ledger,limit):
    state={r["knowledge_id"]:r.get("approval_state","UNAPPROVED") for r in load_jsonl(ledger)}
    eligible=[r for r in rows if state.get(r["knowledge_id"],"UNAPPROVED")!="REJECTED"][:limit]
    return {k:[transform(r,k) for r in eligible] for k in VARIANTS}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data",type=Path,default=Path("results/unapproved_stratified_pairs_v01318.jsonl"))
    p.add_argument("--ledger",type=Path,default=Path("data/unapproved_corpus_ledger_v0139.jsonl"))
    p.add_argument("--base",type=Path,default=Path("model/model-gpu-v1.6.2-online.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--prefix",type=Path,default=Path("results/prefix_ablation_v01325"))
    p.add_argument("--limit",type=int,default=16)
    p.add_argument("--epochs",type=int,default=1)
    p.add_argument("--run",action="store_true")
    a=p.parse_args()
    if a.limit<1 or a.epochs<1:p.error("limit/epochs must be positive")
    dataset=prepare(load_jsonl(a.data),a.ledger,a.limit)
    if len({len(v) for v in dataset.values()})!=1:p.error("unequal variant counts")
    summary={"version":"v0.13.25","pairs":len(dataset["A_LABEL"]),
             "variants":list(VARIANTS),"B_equals_C":"same raw target / metadata external",
             "status":"DRY_RUN","production_unchanged":True}
    if not a.run:
        print(json.dumps(summary,ensure_ascii=False,indent=2));return
    for file in (a.base,a.tokenizer):
        if not file.exists():p.error(f"missing {file}")
    a.prefix.parent.mkdir(parents=True,exist_ok=True)
    training_results={}
    for key,rows in dataset.items():
        data=Path(str(a.prefix)+"_"+key+".jsonl")
        model=Path(str(a.prefix)+"_"+key+".pt")
        state=Path(str(a.prefix)+"_"+key+"_state.json")
        # Same initial checkpoint and independent learning state per variant.
        # Do not overwrite previous experiment results inadvertently.
        if any(path.exists() for path in (data,model,state)):
            p.error(f"existing experiment artifacts for {key}; use a new --prefix")
        data.write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in rows),encoding="utf-8")
        cmd=[sys.executable,"online_train.py","--chat-data",str(data),
             "--base-model",str(a.base),"--tokenizer",str(a.tokenizer),
             "--output",str(model),"--state",str(state),
             "--epochs",str(a.epochs),"--learning-rate","0.000005"]
        exit_code=subprocess.run(cmd,check=False).returncode
        training_results[key]={"returncode":exit_code,"model":str(model),"data":str(data)}
        if exit_code!=0:break
    summary.update(status="TRAINED_CANDIDATES" if len(training_results)==3 and all(r["returncode"]==0 for r in training_results.values()) else "FAILED",
                   "training":training_results)
    report=Path(str(a.prefix)+"_manifest.json")
    report.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    if summary["status"]=="FAILED":raise SystemExit(1)

if __name__=="__main__":main()
