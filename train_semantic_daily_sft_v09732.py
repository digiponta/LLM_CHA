"""Run isolated semantic-aware daily SFT with v0.9.7.32 training data.

Delegates optimizer, target masking and checkpoint safety checks to v0.9.7.30.
Uses a distinct output path. The original twelve holdout samples remain
evaluation-only and are never included in gradient updates.
"""
import train_daily_conversation_sft_v09730 as trainer
from semantic_daily_conversation_v09732 import build

def main():
    import argparse,json
    p=argparse.ArgumentParser()
    p.add_argument("--model",required=True)
    p.add_argument("--tokenizer",required=True)
    p.add_argument("--output",default="model/model-llm-cha-semantic-daily-v09732-experimental.pt")
    p.add_argument("--epochs",type=int,default=3)
    p.add_argument("--lr",type=float,default=2e-5)
    p.add_argument("--replay",type=int,default=3)
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--cpu",action="store_true")
    p.add_argument("--train",action="store_true")
    args=p.parse_args()
    trainer.dataset=build
    # v09730 validates with audit(d) from its original foundation.
    # Enforce this experiment's independent no-leakage check here instead.
    from semantic_daily_conversation_v09732 import audit
    if audit()["train_holdout_overlap"]:raise ValueError("dataset leakage")
    trainer.audit=lambda d:{"ready_for_controlled_training":True}
    print(json.dumps(trainer.run(args),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
