"""Train a broad-dialogue generalization checkpoint without overwriting baselines."""
from __future__ import annotations
import argparse,subprocess,sys
from pathlib import Path

def command(a):
    for name in ("train","val","anchors","base_model","tokenizer"):
        if not Path(getattr(a,name)).is_file():
            raise FileNotFoundError(getattr(a,name))
    if Path(a.base_model).resolve()==Path(a.output).resolve():
        raise ValueError("Refusing to overwrite base checkpoint")
    if a.epochs<1 or a.batch_size<1 or a.anchor_weight<1:
        raise ValueError("Invalid positive training parameter")
    return [sys.executable,"train_nagato_chat.py","--preformatted-prompts",
        "--data",a.train,"--val-data",a.val,
        "--anchor-data",a.anchors,"--anchor-weight",str(a.anchor_weight),
        "--base-model",a.base_model,"--tokenizer",a.tokenizer,
        "--output",a.output,"--epochs",str(a.epochs),
        "--batch-size",str(a.batch_size),
        "--learning-rate",str(a.learning_rate),
        "--lm-head-learning-rate",str(a.lm_head_learning_rate),
        "--trainable-blocks","2","--repeat","1","--persona-weight","1"]
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--train",default="data/dialogue_generalization_v0212/train.jsonl")
    p.add_argument("--val",default="data/dialogue_generalization_v0212/val.jsonl")
    p.add_argument("--anchors",default="data/realpersonachat_quality/persona_anchors_preformatted.jsonl")
    p.add_argument("--base-model",default="model/model-llm-cha-quality-v028.pt")
    p.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--output",default="model/model-llm-cha-generalization-v0212.pt")
    p.add_argument("--epochs",type=int,default=3)
    p.add_argument("--batch-size",type=int,default=8)
    p.add_argument("--anchor-weight",type=int,default=50)
    p.add_argument("--learning-rate",type=float,default=2e-6)
    p.add_argument("--lm-head-learning-rate",type=float,default=3e-7)
    p.add_argument("--dry-run",action="store_true")
    a=p.parse_args()
    cmd=command(a)
    print(subprocess.list2cmdline(cmd),flush=True)
    if not a.dry_run:subprocess.run(cmd,check=True)
if __name__=="__main__":main()
