"""Check small SFT epoch comparison artifacts and summarize teacher-forcing metrics.

Does not train, promote, or overwrite any checkpoint. Requires distinct
checkpoint and state destinations for the two independent experiments.
"""
import argparse,json
from pathlib import Path

def validate_paths(base, model2, model4, state2, state4):
    paths=[Path(x).resolve() for x in (base,model2,model4,state2,state4)]
    if len(set(paths))!=len(paths):raise ValueError("EXPERIMENT_PATH_COLLISION")
    if not paths[0].is_file():raise FileNotFoundError(base)
    return {"status":"PATHS_ISOLATED","base":str(paths[0]),
            "model_2":str(paths[1]),"model_4":str(paths[2]),
            "state_2":str(paths[3]),"state_4":str(paths[4])}

def summarize(diagnostic):
    if diagnostic.get("status")!="TEACHER_FORCED_TOKEN_ANALYSIS":
        raise ValueError("WRONG_REPORT")
    results={}
    for key in ("base","candidate"):
        records=diagnostic.get(key,[])
        if not records:raise ValueError("EMPTY_MODEL_RESULTS")
        results[key]={
            row["question"]:{
                "mean_nll":row["teacher_forced_mean_nll"],
                "top1":row["teacher_forced_top1_count"],
                "tokens":row["target_token_count"],
                "greedy_divergence":row["greedy_first_divergence_position"],
                "greedy_text":row["greedy_text"]
            } for row in records}
    return results

def compare(two,four):
    a=summarize(two);b=summarize(four)
    if set(a["base"])!=set(b["base"]) or set(a["candidate"])!=set(b["candidate"]):
        raise ValueError("QUESTION_SET_MISMATCH")
    rows=[]
    for q in a["candidate"]:
        x=a["candidate"][q];y=b["candidate"][q]
        if x["tokens"]!=y["tokens"]:raise ValueError("REFERENCE_TOKEN_COUNT_MISMATCH")
        rows.append({"question":q,"nll_2":x["mean_nll"],"nll_4":y["mean_nll"],
                     "nll_delta_4_minus_2":y["mean_nll"]-x["mean_nll"],
                     "top1_2":x["top1"],"top1_4":y["top1"],
                     "greedy_2":x["greedy_text"],"greedy_4":y["greedy_text"]})
    return {"status":"EPOCH_2_VS_4_TEACHER_FORCING_COMPARISON",
            "rows":rows,"holdout_naturalness_evaluated":False,
            "production_changed":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--model-2",default="model/daily-sft-2epoch-v013588288.pt")
    p.add_argument("--model-4",default="model/daily-sft-4epoch-v013588288.pt")
    p.add_argument("--state-2",default="results/daily-sft-state-2epoch-v013588288.json")
    p.add_argument("--state-4",default="results/daily-sft-state-4epoch-v013588288.json")
    p.add_argument("--report-2")
    p.add_argument("--report-4")
    p.add_argument("--output",default="results/daily_sft_epoch_comparison_v013588288.json")
    a=p.parse_args()
    check=validate_paths(a.base,a.model_2,a.model_4,a.state_2,a.state_4)
    if bool(a.report_2)!=bool(a.report_4):raise ValueError("BOTH_REPORTS_REQUIRED")
    result=check
    if a.report_2:
        for f in (a.report_2,a.report_4):
            if not Path(f).is_file():raise FileNotFoundError(f)
        two=json.loads(Path(a.report_2).read_text(encoding="utf-8-sig"))
        four=json.loads(Path(a.report_4).read_text(encoding="utf-8-sig"))
        result=compare(two,four)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
