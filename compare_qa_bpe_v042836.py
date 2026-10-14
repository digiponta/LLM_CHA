"""v0.4.28.36: optional LOCAL HuggingFace tokenizer.json BPE input ablation.

Requires pip install tokenizers; no network or automatic model download.
Does not silently assume that arbitrary custom JSON is a HF tokenizer.
"""
import argparse,hashlib,json,statistics
from pathlib import Path
from evaluate_qa_cross_encoder_v042830 import run,split_cases
from diagnose_qa_generalization_v042831 import summarize
from semantic_qa_model_contract_v042828 import design
from train_qa_cross_encoder_v042829 import encode_pair

def load_bpe(path):
    try:
        from tokenizers import Tokenizer
    except ImportError as exc:
        raise ValueError("install optional dependency: python -m pip install tokenizers") from exc
    path=Path(path)
    if not path.is_file() or path.is_symlink():raise ValueError("local tokenizer file required")
    doc=json.loads(path.read_text(encoding="utf-8-sig"))
    if doc.get("model",{}).get("type")!="BPE":
        raise ValueError("not a HuggingFace tokenizers BPE JSON; unsupported format")
    tokenizer=Tokenizer.from_file(str(path))
    size=tokenizer.get_vocab_size(with_added_tokens=True)
    if not 1<=size<=65533:raise ValueError("unsupported tokenizer vocabulary size")
    return tokenizer,size+3

def bpe_encoder(tokenizer,limit=160):
    def encode(q,a):
        cap=(limit-2)//2
        qids=tokenizer.encode(q,add_special_tokens=False).ids[:cap]
        aids=tokenizer.encode(a,add_special_tokens=False).ids[:cap]
        # +3 reserves 0 pad, 1 BOS and 2 separator regardless of tokenizer special IDs.
        ids=[1]+[x+3 for x in qids]+[2]+[x+3 for x in aids]
        seg=[0]*(len(qids)+2)+[1]*len(aids)
        return ids,seg
    return encode

def compare(contract,tokenizer,seeds,split_seed,epochs,device,directory,vocab_size):
    if len(seeds)<2 or len(set(seeds))!=len(seeds):raise ValueError("distinct seeds required")
    train,hold=split_cases(contract["cases"],split_seed)
    if len({x["provisional_chatgpt_label"] for x in hold})!=2:raise ValueError("both holdout classes required")
    paths={(kind,seed):directory/f"qa_bpe_v042836_{kind}_{seed}.pt" for kind in ("char_hash","bpe") for seed in seeds}
    if any(p.exists() or p.is_symlink() for p in paths.values()):raise ValueError("checkpoint path exists")
    expected={(x["id"],x["turn"]) for x in hold}
    records=[]
    for seed in seeds:
        for kind,encoder,size in (("char_hash",encode_pair,4096),("bpe",bpe_encoder(tokenizer),vocab_size)):
            path=paths[kind,seed]
            outcome=run(contract,path,epochs=epochs,device=device,seed=seed,split_seed=split_seed,
              encode_fn=encoder,vocab_size=size)
            present={(r["id"],r["turn"]) for r in outcome["records"] if r["split"]=="INTERNAL_GROUP_HOLDOUT"}
            if present!=expected:raise ValueError("holdout mismatch")
            diagnostic=summarize(outcome)
            records.append({"seed":seed,"representation":kind,
              "holdout_auc":diagnostic["holdout_weak_label_ranking_auc"],
              "train":outcome["train_labeled"],"holdout":outcome["holdout_labeled"],
              "checkpoint_verified":outcome["checkpoint_verified"],
              "checkpoint_sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    paired=[]
    for seed in seeds:
        baseline=next(r["holdout_auc"] for r in records if r["seed"]==seed and r["representation"]=="char_hash")
        bpe=next(r["holdout_auc"] for r in records if r["seed"]==seed and r["representation"]=="bpe")
        paired.append({"seed":seed,"char_hash_auc":baseline,"bpe_auc":bpe,"delta_bpe_minus_char":round(bpe-baseline,6)})
    return {"version":"v0.4.28.36","mode":"LOCAL_BPE_PAIRED_DEVELOPMENT_ABLATION",
      "external_holdout":False,"human_ground_truth":False,"weak_labels":"chatgpt",
      "pretrained_encoder":False,"runtime_modified":False,"threshold_fitted":False,
      "tokenizer_vocab_with_reserved":vocab_size,"split_seed":split_seed,
      "paired_runs":paired,"runs":records,
      "mean_delta_bpe_minus_char":round(statistics.mean(r["delta_bpe_minus_char"] for r in paired),6)}

def main():
    p=argparse.ArgumentParser()
    for n in ("validation","labels","tokenizer","output"):p.add_argument("--"+n,required=True)
    p.add_argument("--checkpoint-dir",default="model/qa_bpe_v042836")
    p.add_argument("--split-seed",type=int,default=20261014)
    p.add_argument("--seeds",default="20261014,20261015,20261016")
    p.add_argument("--epochs",type=int,default=15)
    p.add_argument("--device",choices=["cpu","cuda"],default="cpu")
    a=p.parse_args()
    try:
        seeds=[int(x.strip()) for x in a.seeds.split(",")]
        if not 2<=len(seeds)<=10 or len(set(seeds))!=len(seeds):raise ValueError("2..10 distinct seeds required")
        if not 1<=a.epochs<=100:raise ValueError("epochs outside 1..100")
        inputs=[Path(a.validation),Path(a.labels)];dst=Path(a.output);directory=Path(a.checkpoint_dir)
        if any(not x.is_file() or x.is_symlink() for x in inputs) or dst.exists() or dst.is_symlink():raise ValueError("invalid paths")
        if directory.is_symlink() or (directory.exists() and not directory.is_dir()):raise ValueError("invalid directory")
        tokenizer,size=load_bpe(a.tokenizer)
        contract=design(*[json.loads(x.read_text(encoding="utf-8-sig")) for x in inputs])
        directory.mkdir(parents=True,exist_ok=True)
        result=compare(contract,tokenizer,seeds,a.split_seed,a.epochs,a.device,directory,size)
        result["sha256"]={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in inputs+[Path(a.tokenizer)]}
        dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({"runs":len(result["runs"]),"mean_delta_bpe_minus_char":result["mean_delta_bpe_minus_char"]}))
    except (OSError,ValueError,TypeError,KeyError,ImportError,RuntimeError) as e:p.exit(1,f"BPE ablation failed: {e}\n")
if __name__=="__main__":main()
