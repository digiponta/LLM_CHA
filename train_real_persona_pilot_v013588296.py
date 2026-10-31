"""Guarded launcher for the approved RealPersonaChat pilot training.

Never modifies the production base. Dry-run by default.
"""
import argparse,json,subprocess,sys
from pathlib import Path
from preflight_real_persona_training_v013588295 import preflight

def command(args):
    return [sys.executable,"online_train.py",
        "--chat-data",args.dataset,"--base-model",args.base,
        "--tokenizer",args.tokenizer,"--output",args.output_model,
        "--state",args.state,"--epochs",str(args.epochs),
        "--learning-rate",str(args.learning_rate),
        "--manual-weight","1","--replay-ratio","1.0"]
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--dataset",default="data/real_persona_pilot_v013588293.jsonl")
    p.add_argument("--review",default="results/real_persona_training_review_v013588295.json")
    p.add_argument("--holdout",default="data/daily_conversation_eval_v013588283.json")
    p.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--tokenizer",required=True)
    p.add_argument("--output-model",default="model/real-persona-cp-pilot-v013588296.pt")
    p.add_argument("--state",default="results/real-persona-cp-state-v013588296.json")
    p.add_argument("--epochs",type=int,default=2)
    p.add_argument("--learning-rate",type=float,default=1e-5)
    p.add_argument("--execute",action="store_true")
    a=p.parse_args()
    if not (1<=a.epochs<=4):raise ValueError("epochs must be 1..4")
    if not (0<a.learning_rate<=1e-4):raise ValueError("learning rate out of bounds")
    if not Path(a.tokenizer).is_file():raise FileNotFoundError(a.tokenizer)
    result=preflight(a.dataset,a.review,a.holdout,a.base,a.output_model,a.state)
    report={"status":result["status"],"pair_count":result["pair_count"],
            "errors":result["errors"],"execute_requested":a.execute,
            "command":command(a),"training_started":False}
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if result["status"]!="READY":raise SystemExit(2)
    if not a.execute:return
    completed=subprocess.run(command(a),check=False)
    if completed.returncode:raise SystemExit(completed.returncode)
if __name__=="__main__":main()
