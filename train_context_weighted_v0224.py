"""v0.2.24 SFT wrapper with explicit effective context exposure accounting."""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
from train_nagato_chat import load_pairs

def command(a):
    paths=[a.train,a.context,a.val,a.anchors,a.base_model,a.tokenizer,a.manifest]
    for value in paths:
        if not Path(value).is_file():raise FileNotFoundError(value)
    if Path(a.output).resolve()==Path(a.base_model).resolve():raise ValueError("Cannot overwrite baseline")
    manifest=json.loads(Path(a.manifest).read_text(encoding="utf-8"))
    context_pairs=load_pairs(Path(a.context));train_pairs=load_pairs(Path(a.train))
    if len(context_pairs)!=manifest["unique_context_pairs"] or a.context_weight!=manifest["context_weight"]:
        raise ValueError("Context count or configured weight does not match manifest")
    exposures=len(context_pairs)*a.context_weight
    base=len(train_pairs)
    effective=exposures+base+a.anchor_weight*len(load_pairs(Path(a.anchors)))
    stats={"context_unique":len(context_pairs),"context_exposures_per_epoch":exposures,
           "replay_unique":base,"anchor_exposures_per_epoch":effective-base-exposures,
           "total_exposures_per_epoch":effective,"context_fraction":round(exposures/effective,6)}
    cmd=[sys.executable,"train_nagato_chat.py","--preformatted-prompts",
         "--data",a.train,"--val-data",a.val,"--expansion-data",a.context,
         "--expansion-weight",str(a.context_weight),"--anchor-data",a.anchors,
         "--anchor-weight",str(a.anchor_weight),"--base-model",a.base_model,
         "--tokenizer",a.tokenizer,"--output",a.output,"--epochs",str(a.epochs),
         "--batch-size",str(a.batch_size),"--learning-rate",str(a.learning_rate),
         "--lm-head-learning-rate",str(a.lm_head_learning_rate),
         "--trainable-blocks","2","--repeat","1","--persona-weight","1"]
    return cmd,stats
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--train",default="data/context_weighted_v0224/train.jsonl")
    p.add_argument("--context",default="data/context_weighted_v0224/context.jsonl")
    p.add_argument("--val",default="data/context_weighted_v0224/val.jsonl")
    p.add_argument("--manifest",default="data/context_weighted_v0224/manifest.json")
    p.add_argument("--anchors",default="data/realpersonachat_quality/persona_anchors_preformatted.jsonl")
    p.add_argument("--base-model",default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--output",default="model/model-llm-cha-context-weighted-v0224.pt")
    p.add_argument("--context-weight",type=int,default=60)
    p.add_argument("--anchor-weight",type=int,default=10)
    p.add_argument("--epochs",type=int,default=3)
    p.add_argument("--batch-size",type=int,default=8)
    p.add_argument("--learning-rate",type=float,default=2e-6)
    p.add_argument("--lm-head-learning-rate",type=float,default=3e-7)
    p.add_argument("--dry-run",action="store_true")
    a=p.parse_args()
    if min(a.epochs,a.batch_size,a.context_weight,a.anchor_weight)<1:p.error("Positive parameters required")
    cmd,stats=command(a)
    print("Effective training exposure:",json.dumps(stats,ensure_ascii=False),flush=True)
    print(subprocess.list2cmdline(cmd),flush=True)
    if not a.dry_run:subprocess.run(cmd,check=True)
if __name__=="__main__":main()
