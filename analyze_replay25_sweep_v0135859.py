"""v0.13.58.59: analysis of longer controlled 25%-replay runs.

The trainer remains train_controlled_replay_v0135858.py, preventing subtle
changes in the training algorithm between comparison arms.
"""
import argparse,csv,json
from pathlib import Path

CONDITIONS=((24000,60),(32000,80),(40000,100))
def summarize(paths,output):
    if output.exists():raise FileExistsError(output)
    result=[]
    review=[]
    for budget,updates,path in paths:
        report=json.loads((path/"report.json").read_text(encoding="utf-8-sig"))
        if (report["train_token_budget"]!=budget or report["updates"]!=updates
            or report["replay_ratio"]!=0.25 or report["train_count"]!=56):
            raise ValueError(f"incorrect experiment: {path}")
        measurements=[json.loads(x) for x in (path/"metrics.jsonl").read_text(encoding="utf-8-sig").splitlines() if x.strip()]
        if not measurements or measurements[-1]["updates"]!=updates:raise ValueError("incomplete run")
        if measurements[-1]["train_token_exposures"]!=budget:raise ValueError("incomplete token budget")
        best=min(measurements,key=lambda x:x["validation_nll"])
        final=measurements[-1]
        full=next((m for m in measurements if m["fit"]["token_exact"]==56 and not m["protected_changed_ids"]),None)
        result.append({"train_budget":budget,"updates":updates,
                       "total_exposures":final["train_token_exposures"]+final["replay_token_exposures"],
                       "final_validation_nll":final["validation_nll"],"best_validation_nll":best["validation_nll"],
                       "best_step":best["updates"],"fit_exact":final["fit"]["token_exact"],
                       "holdout_exact":final["holdout"]["token_exact"],
                       "protected_changed_ids":final["protected_changed_ids"],
                       "first_fully_safe_step":full["updates"] if full else None,
                       "elapsed_seconds":final["elapsed_seconds"]})
        for item in final["holdout_generations"]:
            review.append({"train_budget":budget,"updates":updates,"id":item["id"],
                           "reference":item["expected_text"],"generated":item["generated"],
                           "token_exact":item["token_exact_body"],
                           "nfkc_exact":item["nfkc_equal"],"relevance":"","naturalness":"",
                           "factuality":"","repetition":"","human_review_required":True})
    output.mkdir(parents=True,exist_ok=False)
    (output/"summary.json").write_text(json.dumps({"version":"v0.13.58.59","conditions":result,
       "semantic_quality_reviewed":False,"production_approved":False},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with (output/"review.csv").open("w",newline="",encoding="utf-8-sig") as f:
        writer=csv.DictWriter(f,fieldnames=review[0].keys())
        writer.writeheader();writer.writerows(review)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path("results"))
    p.add_argument("--output",type=Path,default=Path("results/replay25_sweep_v0135859_summary"))
    a=p.parse_args()
    summarize([(b,u,a.root/f"replay25_v0135859_t{b}_u{u}") for b,u in CONDITIONS],a.output)
if __name__=="__main__":main()
