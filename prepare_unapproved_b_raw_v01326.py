"""v0.13.26: adopt B_RAW as default unapproved QA training policy.

Model learns natural-language source text only. Knowledge status is external.
Writes candidate QA; never edits the source, ledger or production checkpoint.
"""
import argparse
import json
from pathlib import Path
from unapproved_corpus_learning_v0139 import load_jsonl
from train_prefix_ablation_v01325 import strip_label
from online_train import pair_fingerprint

POLICY="B_RAW"
def convert(rows,ledger):
    approvals={r["knowledge_id"]:r.get("approval_state","UNAPPROVED") for r in load_jsonl(ledger)}
    result=[]
    for row in rows:
        kid=row["knowledge_id"]
        state=approvals.get(kid,row.get("approval_state","UNAPPROVED"))
        if state!="UNAPPROVED":continue
        source=str(row.get("source_text","")).strip()
        target=source or strip_label(str(row.get("assistant","")))
        if not target:continue
        question=str(row.get("user","")).strip()
        if not question:continue
        item={**row,"assistant":target,"source":"corpus-unapproved",
              "approval_state":state,"truth_state":"UNVERIFIED",
              "answer_format":POLICY,"pair_fingerprint":pair_fingerprint(question,target)}
        result.append(item)
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,default=Path("results/unapproved_stratified_pairs_v01318.jsonl"))
    p.add_argument("--ledger",type=Path,default=Path("data/unapproved_corpus_ledger_v0139.jsonl"))
    p.add_argument("--output",type=Path,default=Path("results/unapproved_b_raw_v01326.jsonl"))
    p.add_argument("--write",action="store_true")
    a=p.parse_args()
    if a.output.resolve()==a.input.resolve():p.error("output must differ from input")
    if not a.input.exists():p.error(f"missing input: {a.input}")
    rows=convert(load_jsonl(a.input),a.ledger)
    status={"policy":POLICY,"pairs":len(rows),"unique_knowledge_ids":len({r["knowledge_id"] for r in rows}),
            "write":a.write,"production_unchanged":True,"approval_modified":False,
            "output":str(a.output)}
    if a.write:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in rows),encoding="utf-8")
    print(json.dumps(status,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
