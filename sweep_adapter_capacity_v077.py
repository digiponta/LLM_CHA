"""v0.7.7 — 27-condition isolated adapter capacity sweep.

Each experiment uses the same frozen Base and Candidate Memory, writes a
distinct checkpoint and evaluates its teacher-forced NLL and greedy output.
No knowledge promotion, no approved-store modifications.
"""
import argparse
import csv
import hashlib
import itertools
import json
from pathlib import Path

from train_experimental_adapter_v073 import run as train_adapter
from evaluate_dual_adapter_v074 import run as evaluate_adapter
from diagnose_generation_v076 import run as diagnose_adapter

RANKS=(8,16,32)
EPOCHS=(10,30,100)
LEARNING_RATES=(1e-4,3e-4,1e-3)

def condition_id(rank,epochs,learning_rate):
    return f"r{rank}_e{epochs}_lr{learning_rate:.0e}".replace("+","")

def select_conditions(limit=None):
    combos=list(itertools.product(RANKS,EPOCHS,LEARNING_RATES))
    if limit is not None:
        if limit < 1 or limit > len(combos):raise ValueError("limit must be 1..27")
        return combos[:limit]
    return combos

def summarize(diagnostic,quality,rank,epochs,lr,checkpoint):
    candidates=diagnostic["candidate"]
    experimental=[item["routes"]["experimental"] for item in candidates]
    baseline=[item["routes"]["base"] for item in candidates]
    def exact(rows):
        return sum(bool(x["exact_match"]) for x in rows)/len(rows) if rows else None
    def rank_mean(rows):
        return sum(x["first_reference_token_rank"] for x in rows)/len(rows) if rows else None
    approved=diagnostic["approved"]
    def approved_accuracy(route):
        return (sum(x["routes"][route]["exact_match"] for x in approved)/len(approved)
                if approved else None)
    return {"id":condition_id(rank,epochs,lr),"rank":rank,"epochs":epochs,
      "learning_rate":lr,"candidate_count":len(candidates),"approved_count":len(approved),
      "candidate_exact_base":exact(baseline),"candidate_exact_experimental":exact(experimental),
      "first_token_rank_base":rank_mean(baseline),
      "first_token_rank_experimental":rank_mean(experimental),
      "nll_base":quality["candidate"]["base"]["mean_nll"],
      "nll_experimental":quality["candidate"]["experimental"]["mean_nll"],
      "nll_delta":quality["candidate_nll_delta_experimental_minus_base"],
      "approved_exact_base":approved_accuracy("base"),
      "approved_exact_experimental":approved_accuracy("experimental"),
      "quality_pass":None if not approved else
        (approved_accuracy("experimental")>=approved_accuracy("base") and
         exact(experimental)>exact(baseline)),
      "checkpoint":str(checkpoint)}

def run_sweep(base,tokenizer,approved,candidates,output_dir,limit=None,continue_on_error=True):
    output=Path(output_dir).resolve()
    output.mkdir(parents=True,exist_ok=True)
    summary_path=output/"summary_v077.json"
    csv_path=output/"summary_v077.csv"
    if summary_path.exists() or csv_path.exists():
        raise FileExistsError("sweep summary exists; choose a new output directory")
    rows=[]
    failures=[]
    for rank,epochs,lr in select_conditions(limit):
        name=condition_id(rank,epochs,lr)
        folder=output/name
        checkpoint=folder/"experimental-adapter.pt"
        quality_file=folder/"quality.json"
        diagnostic_file=folder/"diagnostic.json"
        try:
            print(f"[SWEEP] {name}",flush=True)
            train_result=train_adapter(base,tokenizer,approved,candidates,checkpoint,
                                       rank=rank,epochs=epochs,lr=lr)
            quality=evaluate_adapter(base,tokenizer,approved,candidates,checkpoint,quality_file)
            diagnostic=diagnose_adapter(base,tokenizer,approved,candidates,checkpoint,
                                         diagnostic_file)
            row=summarize(diagnostic,quality,rank,epochs,lr,checkpoint)
            row["train_first_loss"]=train_result["first_loss"]
            row["train_last_loss"]=train_result["last_loss"]
            rows.append(row)
            print(f"[RESULT] {name} delta={row['nll_delta']:.6f} "
                  f"exact={row['candidate_exact_experimental']} "
                  f"rank={row['first_token_rank_experimental']}",flush=True)
        except Exception as exc:
            failures.append({"id":name,"error":f"{type(exc).__name__}: {exc}"})
            print(f"[FAILED] {name}: {exc}",flush=True)
            if not continue_on_error:raise
    report={"version":"v0.7.7","requested_conditions":len(select_conditions(limit)),
       "completed":len(rows),"failures":failures,"approved_coverage_sufficient":
       bool(rows and all(row["approved_count"]>0 for row in rows)),
       "quality_pass":None if not rows or not all(row["approved_count"]>0 for row in rows) else
         any(row["quality_pass"] is True for row in rows),
       "notes":"train-set candidate probes are not independent holdout; quality is not approval",
       "rows":rows}
    summary_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if rows:
        with csv_path.open("w",newline="",encoding="utf-8-sig") as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--approved",default="data/approved_v071.jsonl")
    p.add_argument("--candidates",default="data/candidates_v071.jsonl")
    p.add_argument("--output-dir",default="results/adapter_sweep_v077")
    p.add_argument("--limit",type=int,default=None,help="First N experiments for smoke testing (1..27)")
    p.add_argument("--stop-on-error",action="store_true")
    args=p.parse_args()
    report=run_sweep(args.base,args.tokenizer,args.approved,args.candidates,
      args.output_dir,args.limit,not args.stop_on_error)
    print(json.dumps({k:v for k,v in report.items() if k!="rows"},ensure_ascii=False,indent=2))
    raise SystemExit(0 if not report["failures"] else 1)
if __name__=="__main__":main()
