"""v0.2.25 wrapper reusing verified v0.2.24 expansion-weight trainer."""
from __future__ import annotations
import argparse,subprocess,sys,json
from pathlib import Path
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
 p.add_argument("--output",default="model/model-llm-cha-context-generalization-v0225.pt")
 p.add_argument("--context-weight",type=int,default=12)
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
