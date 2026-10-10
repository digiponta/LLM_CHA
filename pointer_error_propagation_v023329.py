"""v0.2.33.29: frozen free-decoding pointer drift and error propagation diagnostic.

Loads the four trained v0.2.33.28 heads. Does not retrain. Logs free
autonomous predicted source indices separately from teacher-forced indices.
"""
import argparse,json,random
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from algorithmic_copy_generalization_v023320 import make_pools
from adaptive_pointer_length_v023326 import prepare
from relative_monotonic_pointer_v023328 import PositionPointer,MODES

def trace(model,head,source,marker,bos,eos,budget=None):
    """Oracle-aligned labels are used for scoring only, never selecting free tokens."""
    n=len(source)
    steps=max(32,n+5) if budget is None else budget
    output=[];last_position=None;free=[]
    with torch.inference_mode():
        for step in range(steps):
            logits=head.position_logits(model,source,output,marker,bos,last_position)
            idx=int(logits.argmax())
            token=eos if idx==n else source[idx]
            free.append({"step":step,"predicted_position":idx,
                         "expected_position":step if step<=n else None,
                         "position_error":idx-step if step<=n else None,
                         "token":token,
                         "gold_token":(source+[eos])[step] if step<=n else None,
                         "token_correct":token==(source+[eos])[step] if step<=n else None})
            output.append(token)
            if token==eos:break
            last_position=idx
        teacher=[]
        for j in range(n+1):
            logits=head.position_logits(model,source,source[:j],marker,bos)
            idx=int(logits.argmax())
            teacher.append({"step":j,"predicted_position":idx,
                            "position_correct":idx==j,
                            "position_error":idx-j,
                            "token_correct":(eos if idx==n else source[idx])==(eos if j==n else source[j])})
    gold=source+[eos]
    first_token_error=next((j for j in range(min(len(output),len(gold)))
                            if output[j]!=gold[j]),None)
    if first_token_error is None and len(output)!=len(gold):
        first_token_error=min(len(output),len(gold))
    first_position_error=next((r["step"] for r in free if r["position_error"] is not None
                               and r["position_error"]!=0),None)
    if eos in output:
        eos_index=output.index(eos)
        eos_class="early" if eos_index<n else "late" if eos_index>n else "correct"
    else:
        eos_index=None;eos_class="missing"
    return {"source":source,"generated":output,"exact":output==gold,
            "first_token_error":first_token_error,"first_position_error":first_position_error,
            "eos_class":eos_class,"eos_index":eos_index,
            "free":free,"teacher":teacher}

def summary(cases):
    total=len(cases)
    def hist(items):
        counts={}
        for x in items:
            key=str(x)
            counts[key]=counts.get(key,0)+1
        return counts
    valid_drift=[abs(x["position_error"]) for r in cases for x in r["free"] if x["position_error"] is not None]
    free_pos=[x for r in cases for x in r["free"] if x["position_error"] is not None]
    teacher=[x for r in cases for x in r["teacher"]]
    first_error_hist=hist(r["first_token_error"] for r in cases)
    eos_hist=hist(r["eos_class"] for r in cases)
    return {"total":total,"exact":sum(r["exact"] for r in cases),
        "first_token_error_hist":first_error_hist,
        "first_position_error_hist":hist(r["first_position_error"] for r in cases),
        "eos_hist":eos_hist,
        "mean_abs_free_position_error":sum(valid_drift)/len(valid_drift) if valid_drift else None,
        "free_position_accuracy":sum(x["position_error"]==0 for x in free_pos)/len(free_pos) if free_pos else None,
        "teacher_position_accuracy":sum(x["position_correct"] for x in teacher)/len(teacher) if teacher else None,
        "cases":cases}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-llm-cha-algorithmic-copy-v023320.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--heads",default="model/relative_monotonic_pointer_v023328")
    p.add_argument("--out",default="results/pointer_error_propagation_v023329.json")
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--train-count",type=int,default=200)
    p.add_argument("--val-count",type=int,default=40)
    p.add_argument("--test-count",type=int,default=40)
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    a=p.parse_args()
    if min(a.train_count,a.val_count,a.test_count)<1:raise ValueError("Invalid counts")
    out=Path(a.out)
    if out.exists():raise FileExistsError(out)
    dev=torch.device("cuda" if a.device=="auto" and torch.cuda.is_available() else "cpu" if a.device=="auto" else a.device)
    model,ckpt=LanguageModel.load_checkpoint(a.base,dev)
    model.eval()
    for param in model.parameters():param.requires_grad_(False)
    tok=Tokenizer.load(a.tokenizer)
    if tok.vocab_size!=model.vocab_size:raise ValueError("Tokenizer mismatch")
    marker=ckpt.get("metadata",{}).get("marker_id",7)
    known,held=make_pools(model.vocab_size)
    data=prepare(a.seed,known,held,a.train_count,a.val_count,a.test_count)
    groups=("test","long","unseen_token_ids","mixed_ids","novel_extra")
    report={}
    for mode in MODES:
        path=Path(a.heads)/(mode+".pt")
        saved=torch.load(path,map_location=dev,weights_only=True)
        if saved["head_type"]!=mode:raise ValueError(f"Mode mismatch: {path}")
        if saved["base_checkpoint"]!=a.base:raise ValueError(f"Base mismatch: {path}")
        head=PositionPointer(model.d_model,mode).to(dev)
        head.load_state_dict(saved["model_state_dict"])
        head.eval()
        report[mode]={"checkpoint":str(path),"best_stage":saved["best_stage"],"groups":{}}
        for group in groups:
            cases=[trace(model,head,row,marker,tok.bos_id,tok.eos_id) for row in data[group]]
            result=summary(cases)
            report[mode]["groups"][group]=result
            print(f"{mode} {group}: exact={result['exact']}/{result['total']} "
                  f"free_pos={result['free_position_accuracy']:.3f} "
                  f"teacher_pos={result['teacher_position_accuracy']:.3f} "
                  f"EOS={result['eos_hist']}")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({"version":"v0.2.33.29","frozen":True,
        "trained_heads":"v0.2.33.28","results":report,
        "limitations":["Free drift is relative to the gold sequential-copy index only for diagnosis",
          "Teacher-forced predictions use gold history and are not autonomous",
          "Repeated IDs may yield a correct token with an incorrect source position",
          "Once the decoder emits EOS it stops, so late error statistics are censored",
          "No retraining; single-seed synthetic evaluation"]},
        ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved",out)
if __name__=="__main__":main()
