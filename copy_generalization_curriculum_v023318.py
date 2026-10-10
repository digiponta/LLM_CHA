"""v0.2.33.18 staged copy curriculum, strict held-out evaluation.

Read-only baseline, isolated output checkpoint. No DSS/Memory/Bridge modifications.
"""
import argparse,hashlib,json,random
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from train_purpose_sft_v02324 import encode_row,loss_rows
from input_output_copy_learning_v02339 import prompt
from generalized_copy_learning_v023316 import split_corpus,exact_generate

COLORS=["赤い","青い","白い","黒い","黄色い","緑の","紫の","茶色い","銀色の","透明な","橙色の","丸い"]
OBJECTS=["本","箱","紙","袋","傘","冊子","ノート","封筒","望遠鏡","容器","顕微鏡","地球儀"]
PLACES=["机","棚","玄関","入口","窓際","台","引き出し","かご","研究室","実験台","廊下","教室"]
ACTIONS=["置きます","運びます","入れます","移します"]
def variants(color,obj,place,action):
    s=f"{color}{obj}"
    return [f"{s}を{place}に{action}。",
            f"{place}に{s}を{action}。",
            f"次に、{s}を{place}に{action}。",
            f"{s}を{place}に{action}。確認します。"]

def make_stage_sets(seed=42,per_stage=320,val_per_stage=48,test_per_stage=48):
    if min(per_stage,val_per_stage,test_per_stage)<1:
        raise ValueError("Counts must be positive")
    rng=random.Random(seed)
    old_train,old_val,old_test=split_corpus(seed=42)
    reserved=set(old_val+old_test)
    seen=set(old_train)
    stages={"lexical":[],"syntactic":[],"sequence":[]}
    candidates={name:[] for name in stages}
    for c in COLORS:
      for o in OBJECTS:
       for p in PLACES:
        for v in ACTIONS:
         # Deliberately exclude the former constrained original pattern in
         # first 8*8*8*4 combinations to preserve old-val control.
         texts=variants(c,o,p,v)
         is_old=(c in COLORS[:8] and o in OBJECTS[:8] and p in PLACES[:8])
         if not is_old:candidates["lexical"].append(texts[0])
         # Distinct syntax with old or new vocabulary.
         candidates["syntactic"].extend(texts[1:3])
         candidates["sequence"].append(texts[3])
    # The old validation/test controls are excluded from all stages.
    for name,pool in candidates.items():
        pool=list(dict.fromkeys(s for s in pool if s not in reserved))
        rng.shuffle(pool)
        desired=per_stage+val_per_stage+test_per_stage
        selected=[s for s in pool if s not in seen][:desired]
        if len(selected)!=desired:raise ValueError(f"Not enough samples in {name}")
        stages[name]={
          "train":selected[:per_stage],
          "val":selected[per_stage:per_stage+val_per_stage],
          "test":selected[per_stage+val_per_stage:]}
        seen.update(selected)
    assert all(not(set(v["train"])&set(v["val"]) or
                    set(v["train"])&set(v["test"]) or
                    set(v["val"])&set(v["test"])) for v in stages.values())
    return stages,(old_val[:20],old_test[:20])

def as_rows(texts):
    return [{"id":hashlib.sha256(s.encode("utf8")).hexdigest()[:16],
             "prompt":prompt(s),"answer":s} for s in texts]

def quick_eval(model,tok,texts,budget):
    model.eval()
    hits=0;examples=[]
    for t in texts:
        correct,out=exact_generate(model,tok,t,budget)
        hits+=int(correct)
        if len(examples)<4:examples.append({"input":t,"output":out,"exact":correct})
    return {"hits":hits,"total":len(texts),"accuracy":hits/len(texts),"examples":examples}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-llm-cha-general-copy-v023316.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--output",default="model/model-llm-cha-copy-curriculum-v023318.pt")
    p.add_argument("--report",default="results/copy_curriculum_v023318.json")
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--epochs-per-stage",type=int,default=2)
    p.add_argument("--train-per-stage",type=int,default=320)
    p.add_argument("--val-per-stage",type=int,default=48)
    p.add_argument("--test-per-stage",type=int,default=48)
    p.add_argument("--lr",type=float,default=2e-5)
    p.add_argument("--head-lr",type=float,default=4e-6)
    p.add_argument("--max-new-tokens",type=int,default=110)
    a=p.parse_args()
    if a.epochs_per_stage<1 or min(a.lr,a.head_lr)<=0 or a.max_new_tokens<1:raise ValueError("Invalid hyperparameters")
    if Path(a.output).exists() or Path(a.report).exists():raise FileExistsError("Refusing to overwrite outputs")
    stages,(control_val,control_test)=make_stage_sets(a.seed,a.train_per_stage,a.val_per_stage,a.test_per_stage)
    random.seed(a.seed);torch.manual_seed(a.seed)
    dev=torch.device("cuda" if a.device=="auto" and torch.cuda.is_available() else "cpu" if a.device=="auto" else a.device)
    tok=Tokenizer.load(a.tokenizer)
    model,_=LanguageModel.load_checkpoint(a.base,dev)
    if model.vocab_size!=tok.vocab_size:raise ValueError("Vocabulary mismatch")
    all_val=[s for group in stages.values() for s in group["val"]]
    all_test=[s for group in stages.values() for s in group["test"]]
    assert not(set(all_val)&set(all_test))
    assert not(set(all_val)&set(control_test)) and not(set(all_test)&set(control_val))
    def encoded(data):return [encode_row(tok,r,model.context_length) for r in as_rows(data)]
    val_pairs=encoded(all_val)
    optimizer=torch.optim.AdamW([
       {"params":[p for n,p in model.named_parameters() if n!="lm_head.weight"],"lr":a.lr},
       {"params":[model.lm_head.weight],"lr":a.head_lr}],weight_decay=.01)
    history=[];best_nll=float("inf");best_state=None;best_tag=None
    cumulative=[]
    # Selection: a common validation set across all curriculum stages.
    for stage_name in ("lexical","syntactic","sequence"):
        cumulative+=stages[stage_name]["train"]
        train_pairs=encoded(cumulative)
        for epoch in range(1,a.epochs_per_stage+1):
            order=list(range(len(train_pairs)));random.shuffle(order)
            model.train();loss_sum=0.
            for idx in order:
                optimizer.zero_grad(set_to_none=True)
                loss=loss_rows(model,[train_pairs[idx]],dev)
                loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
                optimizer.step();loss_sum+=float(loss.detach())
            model.eval()
            with torch.inference_mode():val_nll=float(loss_rows(model,val_pairs,dev))
            record={"stage":stage_name,"epoch":epoch,"train_nll":loss_sum/len(train_pairs),"val_nll":val_nll}
            history.append(record)
            print(f"{stage_name} epoch={epoch} train={record['train_nll']:.4f} val={val_nll:.4f}")
            if val_nll<best_nll:
                best_nll=val_nll;best_tag=(stage_name,epoch)
                best_state={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
    model.load_state_dict(best_state);model.eval()
    results={"control_val":quick_eval(model,tok,control_val,a.max_new_tokens),
             "control_test":quick_eval(model,tok,control_test,a.max_new_tokens)}
    for name,sets in stages.items():
        results[name]={split:quick_eval(model,tok,sets[split],a.max_new_tokens)
                       for split in ("train","val","test")}
        print(name, {s:f"{results[name][s]['hits']}/{results[name][s]['total']}" for s in ("train","val","test")})
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    model.save_checkpoint(a.output,loss=best_nll,
          metadata={"experiment":"v0.2.33.18","best_stage":best_tag[0],
                    "best_stage_epoch":best_tag[1],"experimental_only":True})
    rep={"version":"v0.2.33.18","base":a.base,"best_stage":best_tag[0],
         "best_stage_epoch":best_tag[1],"best_val_nll":best_nll,
         "data_counts":{k:{split:len(v[split]) for split in ("train","val","test")}
                        for k,v in stages.items()},"history":history,"results":results,
         "no_semantic_component_changes":True,"promotion_eligible":False,
         "limitations":["Synthetic task templates remain narrow",
           "Not strict lexical heldout: new items are introduced in stage training",
           "Final test not used for checkpoint selection",
           "One seed; validation reuse may drive selection bias",
           "Symbol-fidelity heldout remains an independent later evaluation"]}
    out=Path(a.report);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved",a.output,a.report)
if __name__=="__main__":main()
