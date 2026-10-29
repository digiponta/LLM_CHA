"""v0.13.58.56: compare runs at a common supervised-token exposure budget,
and export human review of actual free-running holdout generations.

This postprocessor never creates training data or judges semantic quality itself.
"""
import argparse,csv,json
from pathlib import Path

def read_metrics(path):
    rows=[json.loads(s) for s in path.read_text(encoding="utf-8-sig").splitlines() if s.strip()]
    if not rows or rows[0]["step"]!=0:raise ValueError("missing baseline")
    values=[r["supervised_token_exposures"] for r in rows]
    if values!=sorted(values):raise ValueError("unordered token exposure")
    return rows

def select_at_budget(rows,budget):
    eligible=[r for r in rows if r["supervised_token_exposures"]<=budget]
    if not eligible:raise ValueError("nothing inside budget")
    return eligible[-1]

def analyze(inputs,output,budget):
    if output.exists():raise FileExistsError(output)
    experiments={}
    for n,path in inputs:
        experiments[n]=read_metrics(path)
    if not experiments:raise ValueError("no input")
    # All arms must have *measured* data up to the specified budget.
    for n,rows in experiments.items():
        if rows[-1]["supervised_token_exposures"]<budget:
            raise ValueError(f"run {n} has insufficient exposure to compare at budget {budget}")
    selections={n:select_at_budget(rows,budget) for n,rows in experiments.items()}
    source={n:{"measurement_step":r["step"],"exposure":r["supervised_token_exposures"],
               "validation_nll":r["validation_nll"],"fit":r["fit"],
               "holdout":r["holdout"],"protected_changed_ids":r["protected_changed_ids"]}
            for n,r in selections.items()}
    review=[]
    for n,rows in experiments.items():
        for r in rows:
            if r["step"] not in (0,selections[n]["step"],rows[-1]["step"]):continue
            for item in r["holdout_generations"]:
                review.append({"train_count":n,"step":r["step"],"id":item["id"],
                               "expected":item["expected_text"],"generated":item["generated"],
                               "decoded_target":item["decoded_target"],
                               "token_exact":item["token_exact_body"],
                               "nfkc_exact":item["nfkc_equal"],
                               "relevance":"","naturalness":"","factuality":"","repetition":"",
                               "human_review_required":True})
    output.mkdir(parents=True,exist_ok=False)
    (output/"budget_comparison.json").write_text(json.dumps({
        "version":"v0.13.58.56","comparison_type":"nearest_previous_measurement_under_budget",
        "requested_budget":budget,"runs":source,
        "warning":"Measured exposures differ across arms; this is not exactly equal-token comparison.",
        "semantic_quality_evaluated":False,"production_approved":False},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (output/"generation_review.jsonl").write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in review),encoding="utf-8")
    with (output/"generation_review.csv").open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(review[0]) if review else
                              ["train_count","step","id","expected","generated"])
        writer.writeheader();writer.writerows(review)
    return source

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",action="append",required=True,help="N=path/to/metrics.jsonl")
    p.add_argument("--output",type=Path,default=Path("results/four_axes_review_v0135856"))
    p.add_argument("--budget",type=int,default=7920)
    a=p.parse_args()
    paths=[]
    for value in a.input:
        n,sep,path=value.partition("=")
        if not sep or not n.isdigit() or not path:raise ValueError("--input must be N=path")
        paths.append((int(n),Path(path)))
    outcome=analyze(paths,a.output,a.budget)
    print(json.dumps(outcome,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
