"""v0.4.28.34: fixed grouped partition, varying only training randomness.

Uses the v0.4.28.30 run(split_seed=...) backward-compatible extension.
Development weak labels; no generalization/deployment claim.
"""
import argparse,hashlib,json,statistics
from pathlib import Path
from semantic_qa_model_contract_v042828 import design
from evaluate_qa_cross_encoder_v042830 import run,split_cases
from diagnose_qa_generalization_v042831 import summarize

def experiment(contract,seeds,split_seed,epochs,device,checkpoint_dir):
    if len(seeds)<2 or len(seeds)!=len(set(seeds)):raise ValueError("at least 2 distinct training seeds")
    train,hold=split_cases(contract["cases"],split_seed)
    expected_train={(x["id"],x["turn"]) for x in train}
    expected_hold={(x["id"],x["turn"]) for x in hold}
    if not any(x["provisional_chatgpt_label"] is True for x in hold) or not any(x["provisional_chatgpt_label"] is False for x in hold):
        raise ValueError("fixed holdout must contain both provisional classes")
    paths=[checkpoint_dir/f"qa_cross_encoder_fixed_v042834_seed{s}.pt" for s in seeds]
    if any(p.exists() or p.is_symlink() for p in paths):raise ValueError("checkpoint collision")
    rows=[]
    for seed,path in zip(seeds,paths):
        result=run(contract,path,epochs=epochs,device=device,seed=seed,split_seed=split_seed)
        found_train={(r["id"],r["turn"]) for r in result["records"] if r["split"]=="TRAIN"}
        found_hold={(r["id"],r["turn"]) for r in result["records"] if r["split"]=="INTERNAL_GROUP_HOLDOUT"}
        if found_train!=expected_train or found_hold!=expected_hold:
            raise ValueError("split changed between training seeds")
        s=summarize(result)
        rows.append({"train_seed":seed,"split_seed":split_seed,"checkpoint":str(path),
          "checkpoint_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
          "checkpoint_verified":result["checkpoint_verified"],
          "train_labeled":len(found_train),"holdout_labeled":len(found_hold),
          "holdout_positive":s["splits"]["INTERNAL_GROUP_HOLDOUT"]["positive"]["count"],
          "holdout_negative":s["splits"]["INTERNAL_GROUP_HOLDOUT"]["negative"]["count"],
          "holdout_auc":s["holdout_weak_label_ranking_auc"]})
    aucs=[r["holdout_auc"] for r in rows if r["holdout_auc"] is not None]
    return {"version":"v0.4.28.34","mode":"FIXED_SPLIT_TRAINING_SEED_SWEEP",
      "split_seed":split_seed,"train_seeds":seeds,"same_holdout_across_seeds":True,
      "varying_factors":["model_initialization","training_order"],
      "development_only":True,"external_holdout":False,"human_ground_truth":False,
      "runtime_modified":False,"threshold_fitted":False,
      "train_keys_sha256":hashlib.sha256(json.dumps(sorted(expected_train),ensure_ascii=False).encode()).hexdigest(),
      "holdout_keys_sha256":hashlib.sha256(json.dumps(sorted(expected_hold),ensure_ascii=False).encode()).hexdigest(),
      "auc_mean":round(statistics.mean(aucs),6),"auc_std_population":round(statistics.pstdev(aucs),6),
      "auc_min":min(aucs),"auc_max":max(aucs),"runs":rows}

def main():
    p=argparse.ArgumentParser()
    for name in ("validation","labels","output"):p.add_argument("--"+name,required=True)
    p.add_argument("--checkpoint-dir",default="model/qa_fixed_split_v042834")
    p.add_argument("--split-seed",type=int,default=20261014)
    p.add_argument("--seeds",default="20261014,20261015,20261016,20261017,20261018")
    p.add_argument("--epochs",type=int,default=15)
    p.add_argument("--device",choices=["cpu","cuda"],default="cpu")
    a=p.parse_args()
    try:
        seeds=[int(x.strip()) for x in a.seeds.split(",")]
        if not 2<=len(seeds)<=20 or len(set(seeds))!=len(seeds):raise ValueError("2..20 unique seeds required")
        if not 1<=a.epochs<=100:raise ValueError("epochs out of range")
        inputs=[Path(a.validation),Path(a.labels)];dst=Path(a.output);directory=Path(a.checkpoint_dir)
        if any(not x.is_file() or x.is_symlink() for x in inputs) or dst.exists() or dst.is_symlink():raise ValueError("invalid files")
        if directory.is_symlink() or (directory.exists() and not directory.is_dir()):raise ValueError("invalid checkpoint directory")
        contract=design(*[json.loads(x.read_text(encoding="utf-8-sig")) for x in inputs])
        directory.mkdir(parents=True,exist_ok=True)
        result=experiment(contract,seeds,a.split_seed,a.epochs,a.device,directory)
        result["sha256"]={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in inputs}
        dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({k:result[k] for k in ("split_seed","auc_mean","auc_std_population","auc_min","auc_max")}))
    except (OSError,ValueError,KeyError,TypeError,ImportError,RuntimeError) as e:p.exit(1,f"fixed split sweep failed: {e}\n")
if __name__=="__main__":main()
