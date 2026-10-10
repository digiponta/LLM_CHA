"""v0.2.33.21 read-only algorithmic copy failure diagnostics.

Do not train, alter checkpoints, or use test cases for model selection.
"""
import argparse,collections,json,random
from pathlib import Path
import torch
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from algorithmic_copy_generalization_v023320 import make_pools,make_examples,encode_pair,generation

def teacher_metrics(model,seq,marker,bos,eos):
    x,y=encode_pair(seq,marker,bos,eos,model.context_length)
    device=next(model.parameters()).device
    model.eval()
    with torch.inference_mode():
        logits=model(x.unsqueeze(0).to(device))[0]
        mask=y!=-100
        target=y[mask].to(device)
        scores=logits[mask.to(device)]
        top=scores.argmax(-1)
        lp=F.log_softmax(scores,dim=-1)
        ranks=(scores>scores.gather(1,target[:,None])).sum(1)+1
        nll=-lp.gather(1,target[:,None]).squeeze(1)
    return {"top1_accuracy":float((top==target).float().mean()),
            "first_rank":int(ranks[0]),"first_probability":float(lp[0,target[0]].exp()),
            "eos_rank":int(ranks[-1]),"eos_probability":float(lp[-1,target[-1]].exp()),
            "nll":float(nll.mean()),"position_correct":[bool(v) for v in (top==target).tolist()],
            "position_rank":[int(v) for v in ranks.tolist()]}

def classify_failure(out,expected,eos):
    if out==expected:return "exact"
    if eos in out:
        location=out.index(eos)
        if location<len(expected)-1:return "early_eos"
        if location>len(expected)-1:return "late_eos"
    if len(out)>=len(expected) and out[:len(expected)-1]==expected[:-1]:
        return "eos_missing_or_wrong"
    return "content_mismatch"

def diagnose(model,seq,marker,bos,eos,budget):
    generated=generation(model,seq,marker,bos,eos,budget)
    teacher=teacher_metrics(model,seq,marker,bos,eos)
    expected=generated["expected_ids"];actual=generated["generated_ids"]
    first_error=next((i for i in range(min(len(expected),len(actual)))
                      if expected[i]!=actual[i]),min(len(expected),len(actual)))
    if actual==expected:first_error=None
    return {"source_len":len(seq),"source_ids":seq,"teacher":teacher,
            "free":generated,"first_error_position":first_error,
            "failure_type":classify_failure(actual,expected,eos)}

def summarize(cases):
    total=len(cases)
    total_target=sum(len(x["free"]["expected_ids"]) for x in cases)
    correct=sum(sum(x["teacher"]["position_correct"]) for x in cases)
    types=dict(collections.Counter(x["failure_type"] for x in cases))
    return {"total":total,"exact":sum(x["free"]["exact"] for x in cases),
            "exact_rate":sum(x["free"]["exact"] for x in cases)/total if total else None,
            "teacher_token_top1":correct/total_target if total_target else None,
            "mean_prefix_correct":sum(x["free"]["prefix_correct"] for x in cases)/total if total else None,
            "first_error_counts":dict(collections.Counter(str(x["first_error_position"]) for x in cases
                                                       if x["first_error_position"] is not None)),
            "failure_types":types}

def length_sweep(seed,known,per_length=12):
    rng=random.Random(seed)
    out={}
    for length in range(2,19):
        seen=set();rows=[]
        while len(rows)<per_length:
            s=tuple(rng.choice(known) for _ in range(length))
            if s not in seen:seen.add(s);rows.append(list(s))
        out[f"len_{length:02d}"]=rows
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--model",default="model/model-llm-cha-algorithmic-copy-v023320.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--seed",type=int,default=1042)
    p.add_argument("--per-length",type=int,default=12)
    p.add_argument("--out",default="results/algorithmic_copy_errors_v023321.json")
    a=p.parse_args()
    if a.per_length<1:raise ValueError("per-length must be positive")
    out=Path(a.out)
    if out.exists():raise FileExistsError(out)
    device=torch.device("cuda" if a.device=="auto" and torch.cuda.is_available() else "cpu" if a.device=="auto" else a.device)
    tok=Tokenizer.load(a.tokenizer)
    model,ckpt=LanguageModel.load_checkpoint(a.model,device)
    if tok.vocab_size!=model.vocab_size:raise ValueError("Vocab mismatch")
    model.eval()
    meta=ckpt.get("metadata",{})
    marker=meta.get("marker_id",7)
    known=meta.get("known_token_ids",make_pools(model.vocab_size)[0])
    held=meta.get("heldout_token_ids",make_pools(model.vocab_size)[1])
    if set(known)&set(held):raise ValueError("Overlapping token pools")
    fixed=make_examples(42,known,held)
    groups={**length_sweep(a.seed,known,a.per_length),
            "heldout_ids":fixed["unseen_token_ids"],
            "mixed_ids":fixed["mixed_ids"],
            "historical_test":fixed["test"]}
    reports={}
    for name,seqs in groups.items():
        rows=[diagnose(model,s,marker,tok.bos_id,tok.eos_id,max(32,len(s)+5)) for s in seqs]
        summary=summarize(rows)
        reports[name]={"summary":summary,"cases":rows}
        print(f"{name}: exact={summary['exact']}/{summary['total']} "
              f"teacher_top1={summary['teacher_token_top1']:.3f} "
              f"mean_prefix={summary['mean_prefix_correct']:.2f} failures={summary['failure_types']}")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({"version":"v0.2.33.21","checkpoint":a.model,
        "read_only":True,"training_performed":False,"promotion_eligible":False,
        "groups":reports,
        "limitations":["Length sweep is newly sampled but uses familiar token IDs",
                       "Historical groups are reconstructed from original seed and are not new holdout",
                       "Teacher forcing supplies gold prior output IDs; do not interpret as autonomous accuracy",
                       "Error classification is heuristic; EOS-position details are in cases"]},
        ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved",out)
if __name__=="__main__":main()
