"""Pilot multi-turn SFT, checkpoint output kept separate from prior versions."""
from __future__ import annotations
import argparse,subprocess,sys
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base-model",default="model/model-llm-cha-rpc-replay-v021.pt")
    p.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--data",default="data/realpersonachat_multiturn/rpc_multiturn_train.jsonl")
    p.add_argument("--val",default="data/realpersonachat_multiturn/rpc_multiturn_val.jsonl")
    p.add_argument("--output",default="model/model-llm-cha-multiturn-v024.pt")
    p.add_argument("--epochs",type=int,default=2)
    p.add_argument("--batch-size",type=int,default=8)
    p.add_argument("--dry-run",action="store_true")
    a=p.parse_args()
    for file in (a.base_model,a.tokenizer,a.data,a.val):
        if not Path(file).is_file():raise FileNotFoundError(file)
    if Path(a.base_model).resolve()==Path(a.output).resolve():raise ValueError("Refusing base overwrite")
    cmd=[sys.executable,"train_nagato_chat.py","--preformatted-prompts",
         "--base-model",a.base_model,"--tokenizer",a.tokenizer,
         "--data",a.data,"--val-data",a.val,"--output",a.output,
         "--epochs",str(a.epochs),"--batch-size",str(a.batch_size),
         "--learning-rate","3e-6","--lm-head-learning-rate","5e-7",
         "--persona-weight","1","--repeat","1"]
    print(" ".join(cmd),flush=True)
    if not a.dry_run:subprocess.run(cmd,check=True)
if __name__=="__main__":main()
