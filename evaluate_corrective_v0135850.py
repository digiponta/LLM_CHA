"""v0.13.58.50: audit corrective SFT retention and collect *unreviewed* failures.

Reads a local training report. Separately probes retired holdout -> training
questions with the saved candidate checkpoint. Does not change model or
automatically approve any generated corrective training examples.
"""
import argparse,hashlib,json
from pathlib import Path
from train_daily_generation_v0135847 import dataset
from train_iterative_corrective_v0135833 import generate

def read_json(path):return json.loads(path.read_text(encoding="utf-8-sig"))
def read_jsonl(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8-sig").splitlines() if s.strip()]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def inspect(report,source,prior_corrections):
    data=read_json(report)
    train,holdout,protected=dataset(source)
    corrections=read_jsonl(prior_corrections)
    by_user={r["user"]:r for r in train}
    for row in corrections:
        old=by_user.get(row["user"])
        if old is None or old["assistant"]!=row["assistant"]:
            raise ValueError("corrections not included in train: "+row["id"])
    before={x["id"]:x for x in data["holdout_before"]}
    after={x["id"]:x for x in data["holdout_after"]}
    expected={r["id"] for r in holdout}
    if set(before)!=expected or set(after)!=expected:raise ValueError("report does not match current holdout")
    if data.get("source_sha256")!=sha(source):raise ValueError("training report source hash mismatch")
    cases=[]
    for r in holdout:
        a=after[r["id"]];b=before[r["id"]]
        cases.append({"id":r["id"],"question":r["user"],"expected":r["assistant"],
            "before":b["generated"],"after":a["generated"],
            "exact_before":b["generated"].strip()==r["assistant"].strip(),
            "exact_after":a["generated"].strip()==r["assistant"].strip(),
            "changed":b["generated"]!=a["generated"]})
    return data,train,holdout,protected,corrections,cases

def prepare(report,source,corrections,output,candidate=None,tokenizer=None):
    if output.exists():raise FileExistsError(output)
    data,train,holdout,protected,old,cases=inspect(report,source,corrections)
    corrected=[]
    if candidate is not None:
        if tokenizer is None:raise ValueError("tokenizer required")
        if sha(candidate)!=data.get("candidate_sha256"):raise ValueError("checkpoint hash mismatch")
        import torch
        from model import LanguageModel
        from tokenizer_bpe import Tokenizer
        device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model,_=LanguageModel.load_checkpoint(str(candidate),device=device)
        tok=Tokenizer.load(str(tokenizer))
        if model.vocab_size!=tok.vocab_size:raise ValueError("vocabulary mismatch")
        for row in old:
            generated=generate(model,tok,row,64)
            corrected.append({"id":row["source_id"],"question":row["user"],
                "reference":row["assistant"],"candidate_generated":generated,
                "retained_exact":generated.strip()==row["assistant"].strip()})
    # All failed or non-exact new holdout outputs are candidates ONLY.
    proposals=[{"id":"candidate-"+r["id"],"source_id":r["id"],
                "user":r["question"],"assistant":r["expected"],
                "previous_bad_output":r["after"],"split":"candidate",
                "review_state":"REVIEW_REQUIRED","approved_for_training":False}
               for r in cases if not r["exact_after"]]
    summary={"version":"v0.13.58.50","status":"REVIEW_REQUIRED",
             "training_performed":False,"production_approved":False,
             "holdout_independent":False,"new_holdout":cases,
             "retired_holdout_retention":corrected,
             "candidate_count":len(proposals),
             "protected_changed_ids":data.get("protected_changed_ids",[]),
             "candidate_source_sha256":sha(source)}
    output.mkdir(parents=True,exist_ok=False)
    (output/"evaluation.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (output/"review_candidates.jsonl").write_text(
        "".join(json.dumps(r,ensure_ascii=False)+"\n" for r in proposals),encoding="utf-8")
    return summary

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--report",type=Path,default=Path("results/daily_generation_v0135849/report.json"))
    p.add_argument("--source",type=Path,default=Path("data/daily_sft_corrected_v0135849.jsonl"))
    p.add_argument("--corrections",type=Path,default=Path("data/daily_corrective_candidates_v0135849.jsonl"))
    p.add_argument("--candidate",type=Path,default=None)
    p.add_argument("--tokenizer",type=Path,default=None)
    p.add_argument("--output",type=Path,default=Path("results/corrective_review_v0135850"))
    a=p.parse_args()
    out=prepare(a.report,a.source,a.corrections,a.output,a.candidate,a.tokenizer)
    print(json.dumps({"status":out["status"],"new_holdout_count":len(out["new_holdout"]),
                      "retention_probes":len(out["retired_holdout_retention"]),
                      "candidate_count":out["candidate_count"],
                      "output":str(a.output)},ensure_ascii=False))
if __name__=="__main__":main()
