"""v0.4.28.35: paired, fixed-split character-hash vs UTF-8 byte-input ablation.

Neither representation is BPE or pretrained. Same model, split and training
seed per pair. Results remain provisional development-only diagnostics.
"""
import argparse,hashlib,json,statistics
from pathlib import Path
from train_qa_cross_encoder_v042829 import encode_pair
from evaluate_qa_cross_encoder_v042830 import run,split_cases
from diagnose_qa_generalization_v042831 import summarize
from semantic_qa_model_contract_v042828 import design

def encode_utf8(question,answer,limit=160):
    # Reserved ids: padding=0, BOS=1, separator=2, byte 0..255 -> 3..258.
    cap=(limit-2)//2
    q=list(question.encode("utf-8")[:cap])
    a=list(answer.encode("utf-8")[:cap])
    ids=[1]+[x+3 for x in q]+[2]+[x+3 for x in a]
    segments=[0]*(len(q)+2)+[1]*len(a)
    return ids,segments

def compare(contract,seeds,split_seed,epochs,device,directory):
    if len(seeds)<2 or len(set(seeds))!=len(seeds):raise ValueError("requires distinct seeds")
    train,hold=split_cases(contract["cases"],split_seed)
    if not any(x["provisional_chatgpt_label"] is True for x in hold) or not any(x["provisional_chatgpt_label"] is False for x in hold):
        raise ValueError("holdout needs both weak classes")
    modes={"char_hash":encode_pair,"utf8_byte":encode_utf8}
    paths={(mode,seed):directory/f"qa_representation_v042835_{mode}_seed{seed}.pt" for mode in modes for seed in seeds}
    if any(p.exists() or p.is_symlink() for p in paths.values()):raise ValueError("existing checkpoint")
    expected_hold={(x["id"],x["turn"]) for x in hold}
    results=[]
    for seed in seeds:
        for name,encoder in modes.items():
            path=paths[name,seed]
            trial=run(contract,path,epochs=epochs,device=device,seed=seed,split_seed=split_seed,encode_fn=encoder)
            observed={(x["id"],x["turn"]) for x in trial["records"] if x["split"]=="INTERNAL_GROUP_HOLDOUT"}
            if observed!=expected_hold:raise ValueError("holdout drift")
            stats=summarize(trial)
            results.append({"seed":seed,"representation":name,
              "train":trial["train_labeled"],"holdout":trial["holdout_labeled"],
              "holdout_positive":stats["splits"]["INTERNAL_GROUP_HOLDOUT"]["positive"]["count"],
              "holdout_negative":stats["splits"]["INTERNAL_GROUP_HOLDOUT"]["negative"]["count"],
              "internal_weak_label_auc":stats["holdout_weak_label_ranking_auc"],
              "checkpoint_verified":trial["checkpoint_verified"],
              "checkpoint":str(path),"checkpoint_sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    paired=[]
    for seed in seeds:
        left=next(x for x in results if x["seed"]==seed and x["representation"]=="char_hash")
        right=next(x for x in results if x["seed"]==seed and x["representation"]=="utf8_byte")
        paired.append({"seed":seed,"char_hash_auc":left["internal_weak_label_auc"],
          "utf8_byte_auc":right["internal_weak_label_auc"],
          "delta_byte_minus_char":round(right["internal_weak_label_auc"]-left["internal_weak_label_auc"],6)})
    return {"version":"v0.4.28.35","mode":"PAIRED_FIXED_SPLIT_INPUT_REPRESENTATION_ABLATION",
      "representation_choices":["char_hash","utf8_byte"],"bpe_used":False,
      "pretraining_used":False,"human_ground_truth":False,"external_holdout":False,
      "runtime_modified":False,"threshold_fitted":False,
      "split_seed":split_seed,"train_seeds":seeds,"paired_runs":paired,"runs":results,
      "mean_delta_byte_minus_char":round(statistics.mean(x["delta_byte_minus_char"] for x in paired),6),
      "note":"Input truncation and token inventory differ; architecture capacity is fixed; training uses development ChatGPT weak labels. No independent performance claim."}

def main():
    p=argparse.ArgumentParser()
    for arg in ("validation","labels","output"):p.add_argument("--"+arg,required=True)
    p.add_argument("--checkpoint-dir",default="model/qa_repr_v042835")
    p.add_argument("--split-seed",type=int,default=20261014)
    p.add_argument("--seeds",default="20261014,20261015,20261016")
    p.add_argument("--epochs",type=int,default=15)
    p.add_argument("--device",choices=["cpu","cuda"],default="cpu")
    args=p.parse_args()
    try:
        seeds=[int(x.strip()) for x in args.seeds.split(",")]
        if not 2<=len(seeds)<=10 or len(set(seeds))!=len(seeds):raise ValueError("2..10 distinct seeds required")
        if not 1<=args.epochs<=100:raise ValueError("epochs outside 1..100")
        sources=[Path(args.validation),Path(args.labels)]
        dest=Path(args.output);ckpt_dir=Path(args.checkpoint_dir)
        if any(not x.is_file() or x.is_symlink() for x in sources) or dest.exists() or dest.is_symlink():raise ValueError("invalid input/output")
        if ckpt_dir.is_symlink() or (ckpt_dir.exists() and not ckpt_dir.is_dir()):raise ValueError("invalid checkpoint directory")
        contract=design(*[json.loads(x.read_text(encoding="utf-8-sig")) for x in sources])
        ckpt_dir.mkdir(parents=True,exist_ok=True)
        result=compare(contract,seeds,args.split_seed,args.epochs,args.device,ckpt_dir)
        result["sha256"]={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in sources}
        dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({"runs":len(result["runs"]),"mean_delta_byte_minus_char":result["mean_delta_byte_minus_char"]}))
    except (OSError,ValueError,TypeError,KeyError,ImportError,RuntimeError) as e:p.exit(1,f"representation ablation failed: {e}\n")
if __name__=="__main__":main()
