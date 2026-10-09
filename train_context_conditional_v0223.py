"""Small context-conditioned SFT experiment, producing a new checkpoint."""
from __future__ import annotations
import argparse,subprocess,sys
from pathlib import Path
def command(a):
    for key in ("train","val","anchors","base_model","tokenizer"):
        if not Path(getattr(a,key)).is_file():raise FileNotFoundError(getattr(a,key))
    if Path(a.output).resolve()==Path(a.base_model).resolve():raise ValueError("Refusing model overwrite")
    if a.epochs<1 or a.batch_size<1:raise ValueError("Invalid training settings")
    return [sys.executable,"train_nagato_chat.py","--preformatted-prompts",
      "--data",a.train,"--val-data",a.val,"--anchor-data",a.anchors,
      "--anchor-weight","10","--base-model",a.base_model,"--tokenizer",a.tokenizer,
      "--output",a.output,"--epochs",str(a.epochs),"--batch-size",str(a.batch_size),
      "--learning-rate","2e-6","--lm-head-learning-rate","3e-7",
      "--trainable-blocks","2","--repeat","1","--persona-weight","1"]
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--train",default="data/context_conditional_v0223/train.jsonl")
    p.add_argument("--val",default="data/context_conditional_v0223/val.jsonl")
    p.add_argument("--anchors",default="data/realpersonachat_quality/persona_anchors_preformatted.jsonl")
    p.add_argument("--base-model",default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--output",default="model/model-llm-cha-context-conditional-v0223.pt")
    p.add_argument("--epochs",type=int,default=3)
    p.add_argument("--batch-size",type=int,default=8)
    p.add_argument("--dry-run",action="store_true")
    a=p.parse_args();cmd=command(a);print(subprocess.list2cmdline(cmd),flush=True)
    if not a.dry_run:subprocess.run(cmd,check=True)
if __name__=="__main__":main()
