"""v0.4.28.33: multiseed development robustness sweep (not independent evaluation).

Each seed changes BOTH question-group partition and random initialization.
Do not interpret variation as initialization-only sensitivity.
"""
import argparse,hashlib,json,statistics
from pathlib import Path
from semantic_qa_model_contract_v042828 import design
from evaluate_qa_cross_encoder_v042830 import run
from diagnose_qa_generalization_v042831 import summarize

def sweep(contract,seeds,epochs,device,checkpoint_dir):
    if not seeds or len(set(seeds))!=len(seeds):raise ValueError("seeds must be nonempty and unique")
    rows=[]
    for seed in seeds:
        checkpoint=checkpoint_dir/f"qa_cross_encoder_multiseed_v042833_seed{seed}.pt"
        if checkpoint.exists() or checkpoint.is_symlink():raise ValueError("checkpoint already exists")
    for seed in seeds:
        checkpoint=checkpoint_dir/f"qa_cross_encoder_multiseed_v042833_seed{seed}.pt"
        result=run(contract,checkpoint,epochs=epochs,device=device,seed=seed)
        summary=summarize(result)
        hold=summary["splits"]["INTERNAL_GROUP_HOLDOUT"]
        auc=summary["holdout_weak_label_ranking_auc"]
        rows.append({"seed":seed,"checkpoint":str(checkpoint),
          "checkpoint_sha256":hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
          "train_labeled":result["train_labeled"],"holdout_labeled":result["holdout_labeled"],
          "holdout_positive":hold["positive"]["count"],"holdout_negative":hold["negative"]["count"],
          "holdout_pairs":summary["holdout_positive_negative_pairs"],"ranking_auc":auc,
          "checkpoint_verified":result["checkpoint_verified"]})
    measured=[r["ranking_auc"] for r in rows if r["ranking_auc"] is not None]
    return {"version":"v0.4.28.33","mode":"MULTISEED_INTERNAL_DEVELOPMENT_SWEEP",
      "human_ground_truth":False,"external_holdout":False,"runtime_modified":False,
      "threshold_fitted":False,"same_holdout_across_seeds":False,
      "changes_between_seeds":["grouped_split","model_initialization","training_order"],
      "epochs":epochs,"seeds":seeds,"runs":rows,"auc_defined_runs":len(measured),
      "auc_undefined_runs":len(rows)-len(measured),
      "auc_mean":round(statistics.mean(measured),6) if measured else None,
      "auc_min":min(measured) if measured else None,
      "auc_max":max(measured) if measured else None,
      "note":"Summary is descriptive of different internal partitions and weak ChatGPT labels; not external test accuracy."}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--validation",required=True)
    parser.add_argument("--labels",required=True)
    parser.add_argument("--output",required=True)
    parser.add_argument("--checkpoint-dir",default="model/qa_multiseed_v042833")
    parser.add_argument("--seeds",default="20261014,20261015,20261016,20261017,20261018")
    parser.add_argument("--epochs",type=int,default=15)
    parser.add_argument("--device",choices=["cpu","cuda"],default="cpu")
    a=parser.parse_args()
    try:
        seeds=[int(s.strip()) for s in a.seeds.split(",")]
        if not 2<=len(seeds)<=20 or len(set(seeds))!=len(seeds):raise ValueError("2..20 distinct seeds required")
        if not 1<=a.epochs<=100:raise ValueError("epochs must be 1..100")
        inputs=[Path(a.validation),Path(a.labels)]
        output=Path(a.output);ckpt_dir=Path(a.checkpoint_dir)
        if any(not f.is_file() or f.is_symlink() for f in inputs) or output.exists() or output.is_symlink():
            raise ValueError("invalid source/output")
        if ckpt_dir.is_symlink() or (ckpt_dir.exists() and not ckpt_dir.is_dir()):
            raise ValueError("invalid checkpoint directory")
        contract=design(*[json.loads(f.read_text(encoding="utf-8-sig")) for f in inputs])
        ckpt_dir.mkdir(parents=True,exist_ok=True)
        result=sweep(contract,seeds,a.epochs,a.device,ckpt_dir)
        result["sha256"]={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in inputs}
        output.parent.mkdir(parents=True,exist_ok=True)
        with output.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({k:result[k] for k in ("auc_defined_runs","auc_undefined_runs","auc_mean","auc_min","auc_max")}))
    except (OSError,ValueError,TypeError,KeyError,ImportError,RuntimeError) as e:
        parser.exit(1,f"multiseed sweep failed: {e}\n")
if __name__=="__main__":main()
