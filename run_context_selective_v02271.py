"""v0.2.27.1 launch: same exposures as v0.2.27, selective initiation only."""
import argparse
import subprocess
import sys
import json
from train_context_weighted_v0224 import command

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--train",default="data/context_generalization_v0225/train.jsonl")
    p.add_argument("--context",default="data/context_generalization_v0225/context.jsonl")
    p.add_argument("--val",default="data/context_generalization_v0225/val.jsonl")
    p.add_argument("--manifest",default="data/context_generalization_v0225/manifest.json")
    p.add_argument("--anchors",default="data/realpersonachat_quality/persona_anchors_preformatted.jsonl")
    p.add_argument("--base-model",default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--output",default="model/model-llm-cha-context-selective-v02271.pt")
    p.add_argument("--context-weight",type=int,default=12)
    p.add_argument("--anchor-weight",type=int,default=10)
    p.add_argument("--epochs",type=int,default=3)
    p.add_argument("--batch-size",type=int,default=8)
    p.add_argument("--learning-rate",type=float,default=2e-6)
    p.add_argument("--lm-head-learning-rate",type=float,default=3e-7)
    p.add_argument("--init-k",type=int,default=8)
    p.add_argument("--init-weight",type=float,default=0.5)
    p.add_argument("--dry-run",action="store_true")
    a=p.parse_args()
    if a.init_k<1 or not 0<=a.init_weight<=10:
        p.error("invalid initiation hyperparameters")
    cmd,stats=command(a)
    if cmd[1]!="train_nagato_chat.py":
        raise RuntimeError("unexpected upstream trainer")
    cmd[1]="train_context_selective_v02271.py"
    cmd+=["--context-selective","--init-k",str(a.init_k),"--init-weight",str(a.init_weight)]
    print("Exposures:",json.dumps(stats,ensure_ascii=False),flush=True)
    print("Command:",subprocess.list2cmdline(cmd),flush=True)
    if not a.dry_run:
        subprocess.run(cmd,check=True)

if __name__=="__main__":
    main()
