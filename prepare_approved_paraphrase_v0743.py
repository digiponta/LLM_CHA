"""v0.7.43: Approved-ID-bound question paraphrase experiment.

Prepare proposed supervised training pairs and strictly separate holdouts.
Does not mutate trusted learning history or model weights by itself.
"""
import argparse,json,hashlib
from pathlib import Path
from approved_semantic_sleep_v0740 import _load_jsonl

def forms(subject):
    return {
        "train":[f"{subject}の原文記述は",f"{subject}の特性は",f"{subject}について説明して"],
        "holdout":[f"{subject}について何が書かれている？",f"{subject}に関する記述を教えて"],
    }

def prepare(rows):
    train=[];holdout=[]
    for row in rows:
        question=row["user"]
        if not (row["question"].startswith("原文証拠：") and " #" in row["question"]):
            continue
        subject=row["question"][len("原文証拠："):].rsplit(" #",1)[0]
        samples=forms(subject)
        if len(set(samples["train"]) & set(samples["holdout"])):raise ValueError("split leakage")
        answer=row["assistant"]
        for split,target in (("train",train),("holdout",holdout)):
            for q in samples[split]:
                target.append({"approved_id":row["id"],"question":q,"answer":answer,
                               "subject":subject,"split":split,"source_id":row["source_id"]})
    return {"train":train,"holdout":holdout}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ledger",default="data/approved_semantic_memory_v0740.jsonl")
    p.add_argument("--output",default="results/approved_paraphrase_v0743.json")
    args=p.parse_args()
    rows=_load_jsonl(args.ledger)
    prepared=prepare(rows)
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    if out.resolve()==Path(args.ledger).resolve():raise ValueError("output is input")
    out.write_text(json.dumps({"version":"v0.7.43",**prepared},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"train":len(prepared["train"]),"holdout":len(prepared["holdout"]),
                      "output":str(out)},ensure_ascii=False))
if __name__=="__main__":main()
