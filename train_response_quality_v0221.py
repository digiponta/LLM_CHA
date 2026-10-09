"""v0.2.21 targeted context-aware response SFT, not raw language pretraining."""
from __future__ import annotations
import argparse,subprocess,sys
from pathlib import Path

def command(a):
    for key in ("train","val","base_model","tokenizer","anchors"):
        if not Path(getattr(a,key)).is_file():raise FileNotFoundError(getattr(a,key))
    if Path(a.output).resolve()==Path(a.base_model).resolve():
        raise ValueError("Output cannot overwrite base model")
    if a.epochs<1 or a.batch_size<1 or a.anchor_weight<1:raise ValueError("Invalid training parameter")
    return [sys.executable,"train_nagato_chat.py","--preformatted-prompts",
            "--data",a.train,"--val-data",a.val,
            "--anchor-data",a.anchors,"--anchor-weight",str(a.anchor_weight),
            "--base-model",a.base_model,"--tokenizer",a.tokenizer,
            "--output",a.output,"--epochs",str(a.epochs),
            "--batch-size",str(a.batch_size),"--learning-rate",str(a.learning_rate),
            "--lm-head-learning-rate",str(a.lm_head_learning_rate),
            "--trainable-blocks","2","--repeat","1","--persona-weight","1"]
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--train",default="data/response_quality_v021/train.jsonl")
    p.add_argument("--val",default="data/response_quality_v021/val.jsonl")
    p.add_argument("--anchors",default="data/realpersonachat_quality/persona_anchors_preformatted.jsonl")
    p.add_argument("--base-model",default="model/model-llm-cha-foundation-dialogue-v0218.pt")
    p.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--output",default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--epochs",type=int,default=3)
    p.add_argument("--batch-size",type=int,default=8)
    p.add_argument("--anchor-weight",type=int,default=10)
    p.add_argument("--learning-rate",type=float,default=2e-6)
    p.add_argument("--lm-head-learning-rate",type=float,default=3e-7)
    p.add_argument("--dry-run",action="store_true")
    a=p.parse_args();cmd=command(a)
    print(subprocess.list2cmdline(cmd),flush=True)
    if not a.dry_run:subprocess.run(cmd,check=True)
if __name__=="__main__":main()
