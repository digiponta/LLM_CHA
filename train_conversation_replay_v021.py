"""Controlled v0.2.1 SFT: RealPersonaChat subset + identity/conversation replay.

Uses existing train_nagato_chat.py --anchor-data/--anchor-weight; does not
overwrite source checkpoints or write Semantic Memory.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import sys

def command(args):
    inputs=[args.base_model,args.tokenizer,args.train,args.val,args.anchors]
    for path in inputs:
        if not Path(path).is_file():
            raise FileNotFoundError(f"Missing: {path}")
    if Path(args.base_model).resolve()==Path(args.output).resolve():
        raise ValueError("Refusing to overwrite base model")
    if args.anchor_weight < 1 or args.epochs < 1: raise ValueError("Invalid training settings")
    return [sys.executable,"train_nagato_chat.py",
        "--data",args.train, "--val-data",args.val,
        "--anchor-data",args.anchors, "--anchor-weight",str(args.anchor_weight),
        "--base-model",args.base_model,"--tokenizer",args.tokenizer,
        "--output",args.output,"--epochs",str(args.epochs),
        "--batch-size",str(args.batch_size),
        "--learning-rate",str(args.learning_rate),
        "--lm-head-learning-rate",str(args.lm_head_learning_rate),
        "--trainable-blocks",str(args.trainable_blocks),
        "--repeat","1","--persona-weight","1"]
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--train",default="data/realpersonachat_replay/rpc_replay_train.jsonl")
    p.add_argument("--anchors",default="data/realpersonachat_replay/rpc_replay_anchors.jsonl")
    p.add_argument("--val",default="data/realpersonachat/rpc_val.jsonl")
    p.add_argument("--base-model",default="../LLM_TRY/model/model-llm-try-nagato-chat-v94.pt")
    p.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--output",default="model/model-llm-cha-rpc-replay-v021.pt")
    p.add_argument("--epochs",type=int,default=3)
    p.add_argument("--batch-size",type=int,default=8)
    p.add_argument("--anchor-weight",type=int,default=300)
    p.add_argument("--learning-rate",type=float,default=5e-6)
    p.add_argument("--lm-head-learning-rate",type=float,default=1e-6)
    p.add_argument("--trainable-blocks",type=int,default=2)
    p.add_argument("--dry-run",action="store_true")
    args=p.parse_args()
    cmd=command(args)
    print("Command:",subprocess.list2cmdline(cmd),flush=True)
    if not args.dry_run: subprocess.run(cmd,check=True)
if __name__=="__main__":main()
