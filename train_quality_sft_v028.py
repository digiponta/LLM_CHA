"""Launch v0.2.8 high-information dialogue SFT with persona replay."""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

def command(a):
    for name in ("train","val","anchors","base_model","tokenizer"):
        if not Path(getattr(a,name)).is_file():raise FileNotFoundError(getattr(a,name))
    if Path(a.output).resolve()==Path(a.base_model).resolve():raise ValueError("Base model may not be overwritten")
    return [sys.executable,"train_nagato_chat.py","--preformatted-prompts",
        "--data",a.train,"--val-data",a.val,"--anchor-data",a.anchors,
        "--anchor-weight",str(a.anchor_weight),"--base-model",a.base_model,
        "--tokenizer",a.tokenizer,"--output",a.output,
        "--epochs",str(a.epochs),"--batch-size",str(a.batch_size),
        "--learning-rate",str(a.learning_rate),
        "--lm-head-learning-rate",str(a.lm_head_learning_rate),
        "--trainable-blocks","2","--persona-weight","1","--repeat","1"]
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--train",default="data/realpersonachat_quality/quality_train.jsonl")
    p.add_argument("--val",default="data/realpersonachat_multiturn/rpc_multiturn_val.jsonl")
    p.add_argument("--anchors",default="data/realpersonachat_quality/persona_anchors_preformatted.jsonl")
    p.add_argument("--base-model",default="model/model-llm-cha-rpc-replay-v021.pt")
    p.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--output",default="model/model-llm-cha-quality-v028.pt")
    p.add_argument("--epochs",type=int,default=3)
    p.add_argument("--batch-size",type=int,default=8)
    p.add_argument("--anchor-weight",type=int,default=250)
    p.add_argument("--learning-rate",type=float,default=3e-6)
    p.add_argument("--lm-head-learning-rate",type=float,default=5e-7)
    p.add_argument("--dry-run",action="store_true")
    a=p.parse_args()
    if a.epochs<1 or a.anchor_weight<1:raise ValueError("Positive epochs and anchor weight required")
    cmd=command(a)
    print("Command:",subprocess.list2cmdline(cmd),flush=True)
    if not a.dry_run:subprocess.run(cmd,check=True)
if __name__=="__main__":main()
