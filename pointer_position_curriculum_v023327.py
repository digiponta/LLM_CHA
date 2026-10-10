"""v0.2.33.27: stage-preserving pointer position and length curriculum analysis.

Train 3 pointer heads with the same starting weights/data, store EVERY stage,
select by short validation vs balanced (short+long) validation separately.
No evaluation-set-guided checkpoint selection, no base-model updates.
"""
import argparse,copy,json,random
from pathlib import Path
import torch
from pointer_copy_v023325 import PointerHead,predict
from adaptive_pointer_length_v023326 import AdaptiveHead,sequences,prepare,position_diagnostics
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from algorithmic_copy_generalization_v023320 import make_pools

def position_profile(model,head,examples,marker,bos,eos):
    positions={}
    repeated={"repeat": [0,0], "unique":[0,0]}
    with torch.inference_mode():
        for src in examples:
            has_repeat=len(src)!=len(set(src))
            group="repeat" if has_repeat else "unique"
            for j in range(len(src)+1):
                _,score=head.distribution(model,src,src[:j],marker,bos,eos)
                predicted=int(score.argmax())
                success=predicted==j
                k=str(j)
                row=positions.setdefault(k,{"correct":0,"total":0})
                row["correct"]+=int(success);row["total"]+=1
                repeated[group][0]+=int(success);repeated[group][1]+=1
    return {"by_position":positions,
            "by_repetition":{k:{"correct":v[0],"total":v[1]} for k,v in repeated.items()}}

def evaluate_stage(model,head,group,marker,bos,eos):
    profile=position_diagnostics(model,head,group,marker,bos,eos)
    breakdown=position_profile(model,head,group,marker,bos,eos)
    return {"free_exact":profile["free_exact"],"total":profile["total"],
            "teacher_position_accuracy":profile["teacher_pointer_position_accuracy"],
            "teacher_eos_accuracy":profile["teacher_eos_position_accuracy"],
            **breakdown}

def loss_mean(model,head,examples,marker,bos,eos):
    head.eval()
    with torch.no_grad():
        return sum(float(head.loss_for(model,s,marker,bos,eos)) for s in examples)/len(examples)

def run_arm(model,head,stages,validation,tests,marker,bos,eos,lr,seed,
            save_dir,name):
    opt=torch.optim.AdamW(head.parameters(),lr=lr,weight_decay=.001)
    results=[]
    for step,examples in enumerate(stages,1):
        head.train()
        indices=list(range(len(examples)))
        random.Random(seed+step).shuffle(indices)
        total=0.
        for index in indices:
            opt.zero_grad(set_to_none=True)
            err=head.loss_for(model,examples[index],marker,bos,eos)
            err.backward()
            torch.nn.utils.clip_grad_norm_(head.parameters(),1.)
            opt.step()
            total+=float(err.detach())
        val={key:loss_mean(model,head,v,marker,bos,eos) for key,v in validation.items()}
        # Equal-weight across validation distributions, not across tokens.
        balanced=(val["short"]+val["long"])/2
        scores={key:evaluate_stage(model,head,values,marker,bos,eos)
                for key,values in tests.items()}
        path=save_dir/(f"{name}-stage{step}.pt")
        torch.save({"version":"v0.2.33.27","head_type":name,
                    "stage":step,"model_state_dict":head.state_dict(),
                    "validation_loss":val,"balanced_val_loss":balanced},
                   path)
        result={"stage":step,"train_loss":total/len(examples),
                "validation_loss":val,"balanced_val_loss":balanced,
                "evaluation":scores,"checkpoint":str(path)}
        results.append(result)
        print(f"{name} stage={step} short_val={val['short']:.4f} "
              f"long_val={val['long']:.4f} balanced_val={balanced:.4f} "
              f"long_exact={scores['long']['free_exact']}/{scores['long']['total']} "
              f"long_pos={scores['long']['teacher_position_accuracy']:.3f}")
    short_best=min(results,key=lambda r:r["validation_loss"]["short"])["stage"]
    balanced_best=min(results,key=lambda r:r["balanced_val_loss"])["stage"]
    return {"stages":results,"short_selected_stage":short_best,
            "balanced_selected_stage":balanced_best}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-llm-cha-algorithmic-copy-v023320.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--train-count",type=int,default=200)
    p.add_argument("--val-count",type=int,default=40)
    p.add_argument("--test-count",type=int,default=40)
    p.add_argument("--lr",type=float,default=.001)
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--out",default="results/pointer_position_curriculum_v023327.json")
    p.add_argument("--checkpoint-dir",default="model/pointer_position_curriculum_v023327")
    a=p.parse_args()
    if min(a.train_count,a.val_count,a.test_count)<1 or a.lr<=0:raise ValueError("Invalid args")
    out=Path(a.out);directory=Path(a.checkpoint_dir)
    if out.exists() or directory.exists():raise FileExistsError("Refusing overwrite")
    dev=torch.device("cuda" if a.device=="auto" and torch.cuda.is_available() else "cpu" if a.device=="auto" else a.device)
    model,ckpt=LanguageModel.load_checkpoint(a.base,dev)
    model.eval()
    for parameter in model.parameters():parameter.requires_grad_(False)
    tok=Tokenizer.load(a.tokenizer)
    if tok.vocab_size!=model.vocab_size:raise ValueError("Tokenizer mismatch")
    known,held=make_pools(model.vocab_size)
    marker=ckpt.get("metadata",{}).get("marker_id",7)
    data=prepare(a.seed,known,held,a.train_count,a.val_count,a.test_count)
    # This long validation is independent of the "long" diagnostic test set,
    # train data, and short validation.
    exclusions=[s for group in data.values() for s in group]
    long_val=sequences(a.seed+999,known,a.val_count,12,18,exclusions)
    val={"short":data["val"],"long":long_val}
    tests={k:data[k] for k in ("test","long","unseen_token_ids","mixed_ids","novel_extra")}
    stages=[data["train_short"],data["train_long"],data["train_long"]]
    directory.mkdir(parents=True,exist_ok=False)
    results={}
    for name in ("pointer","hybrid","adaptive"):
        torch.manual_seed(a.seed)
        head=(AdaptiveHead(model.d_model) if name=="adaptive" else PointerHead(model.d_model,name)).to(dev)
        results[name]=run_arm(model,head,stages,val,tests,marker,tok.bos_id,tok.eos_id,
                              a.lr,a.seed,directory,name)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({"version":"v0.2.33.27","base":a.base,"frozen_backbone":True,
        "results":results,"selection_policy":"short or equal-weight short+long validation",
        "limitations":["Stage 3 repeats the same train-long data as Stage 2",
          "All evaluation results are diagnostic, NOT used for stage selection",
          "Teacher-forced pointer position accuracy is not free generation",
          "Repeated IDs make token identity copying easier than strict position matching",
          "Equal-weight balanced validation still depends on the chosen distributions",
          "Single seed, synthetic token task; no language/semantic conclusion"]},
        ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved",out)
if __name__=="__main__":main()
