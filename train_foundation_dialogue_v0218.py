"""v0.2.18 two-stage controlled Japanese foundation -> dialogue SFT pilot.

Dry-run prints both commands. GPU training is local-only; no checkpoint is
asserted to exist merely by running this wrapper.
"""
from __future__ import annotations
import argparse,subprocess,sys
from pathlib import Path

def commands(a):
    required=(a.corpus,a.base_model,a.tokenizer,a.dialogue_train,a.dialogue_val,a.anchors)
    for path in required:
        if not Path(path).is_file():raise FileNotFoundError(path)
    if len({Path(a.base_model).resolve(),Path(a.cpt_output).resolve(),Path(a.sft_output).resolve()})!=3:
        raise ValueError("Outputs must be distinct from each other and the base model")
    cpt=[sys.executable,"train_nagato.py","--data",a.corpus,"--tokenizer",a.tokenizer,
         "--base-model",a.base_model,"--output",a.cpt_output,
         "--epochs",str(a.cpt_epochs),"--learning-rate","5e-6",
         "--batch-size","8","--block-size","128","--stride","128",
         "--validation-ratio","0.1","--patience","1"]
    sft=[sys.executable,"train_nagato_chat.py","--preformatted-prompts",
         "--data",a.dialogue_train,"--val-data",a.dialogue_val,
         "--anchor-data",a.anchors,"--anchor-weight","50",
         "--base-model",a.cpt_output,"--tokenizer",a.tokenizer,"--output",a.sft_output,
         "--epochs",str(a.sft_epochs),"--batch-size","8",
         "--learning-rate","2e-6","--lm-head-learning-rate","3e-7",
         "--trainable-blocks","2","--repeat","1","--persona-weight","1"]
    return cpt,sft
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--corpus",default="data/japanese_foundation_v0218.txt")
    p.add_argument("--base-model",default="model/model-llm-cha-quality-v028.pt")
    p.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--dialogue-train",default="data/dialogue_generalization_v0212/train.jsonl")
    p.add_argument("--dialogue-val",default="data/dialogue_generalization_v0212/val.jsonl")
    p.add_argument("--anchors",default="data/realpersonachat_quality/persona_anchors_preformatted.jsonl")
    p.add_argument("--cpt-output",default="model/model-llm-cha-foundation-v0218.pt")
    p.add_argument("--sft-output",default="model/model-llm-cha-foundation-dialogue-v0218.pt")
    p.add_argument("--cpt-epochs",type=int,default=1)
    p.add_argument("--sft-epochs",type=int,default=2)
    p.add_argument("--stage",choices=("both","cpt","sft"),default="both")
    p.add_argument("--dry-run",action="store_true")
    a=p.parse_args()
    if min(a.cpt_epochs,a.sft_epochs)<1:p.error("epochs must be positive")
    cpt,sft=commands(a)
    stages=([cpt,sft] if a.stage=="both" else [cpt] if a.stage=="cpt" else [sft])
    for cmd in stages:
        print(subprocess.list2cmdline(cmd),flush=True)
        if not a.dry_run:subprocess.run(cmd,check=True)
if __name__=="__main__":main()
