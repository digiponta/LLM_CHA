"""v0.6.32: read-only paired model quality and forgetting gate.

Measures direct LM behavior, not the full chat.py retrieval/persona routing.
No checkpoints or learning state are written.
"""
import argparse
import json
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer

DEFAULT_CASES=[
 {"id":"identity","group":"persona","prompt":"貴方は誰","expected_any":["長門有希","長門"]},
 {"id":"greeting","group":"persona","prompt":"こんばんは","expected_any":["こんばんは","夜"]},
 {"id":"cat","group":"known","prompt":"猫","expected_any":["猫","ネコ","ねこ"]},
]
def score(answer,case):
    terms=case["expected_any"]
    return bool(terms) and any(t in answer for t in terms)

def compare(before,after,cases,max_drop=0.0,min_new_accuracy=0.0):
    details=[]
    for case in cases:
        a,b=bool(before[case["id"]]),bool(after[case["id"]])
        details.append({"id":case["id"],"group":case["group"],
                        "before":a,"after":b,"forgotten":a and not b})
    protected=[r for r in details if r["group"]!="new"]
    new=[r for r in details if r["group"]=="new"]
    base_correct=sum(r["before"] for r in protected)
    lost=sum(r["forgotten"] for r in protected)
    forgetting=lost/base_correct if base_correct else None
    new_accuracy=sum(r["after"] for r in new)/len(new) if new else None
    gate=(bool(protected) and base_correct>0 and forgetting is not None
          and forgetting<=max_drop and bool(new) and new_accuracy>=min_new_accuracy)
    return {"pass":bool(gate),"forgetting_rate":forgetting,
            "new_accuracy":new_accuracy,"protected_pre_correct":base_correct,
            "forgotten_count":lost,"details":details,
            "limitations":"Direct model generation only; no chat.py router quality assertion."}

@torch.no_grad()
def infer(model,tokenizer,prompt,max_tokens):
    prefix=tokenizer.encode("人: "+prompt+"\nAI: ",add_bos=True)
    tokens=model.generate(prefix,max_new_tokens=max_tokens,eos_id=tokenizer.eos_id,
                          temperature=0.0,top_k=1)
    return tokenizer.decode(tokens[len(prefix):]).strip()

def load_cases(path):
    if path is None:return list(DEFAULT_CASES)
    value=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value,list) or not value:raise ValueError("nonempty cases list required")
    ids=set()
    for c in value:
        if not all(k in c for k in ("id","group","prompt","expected_any")):raise ValueError("incomplete case")
        if c["id"] in ids:raise ValueError("duplicate id")
        ids.add(c["id"])
        if c["group"] not in ("persona","known","new"):raise ValueError("invalid group")
    return value

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--before",required=True)
    p.add_argument("--after",required=True)
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--cases",required=True,help="Explicit protected/new QA case JSON")
    p.add_argument("--max-tokens",type=int,default=64)
    p.add_argument("--max-forgetting",type=float,default=0.0)
    p.add_argument("--min-new-accuracy",type=float,default=1.0)
    p.add_argument("--output",default="results/quality_gate_v0632.json")
    args=p.parse_args()
    for label, candidate in (("before",args.before),("after",args.after),("tokenizer",args.tokenizer),("cases",args.cases)):
        if not Path(candidate).is_file():
            raise SystemExit("Missing {} file: {}. The --after checkpoint must first be created by online_train.py; this evaluator does not train.".format(label,candidate))
    cases=load_cases(args.cases)
    if not any(c["group"]=="new" for c in cases):raise ValueError("at least one new knowledge case required")
    tokenizer=Tokenizer.load(args.tokenizer)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    before,_=LanguageModel.load_checkpoint(args.before,device=device)
    after,_=LanguageModel.load_checkpoint(args.after,device=device)
    if before.vocab_size!=tokenizer.vocab_size or after.vocab_size!=tokenizer.vocab_size:
        raise ValueError("tokenizer/model vocabulary mismatch")
    answers={}
    assessments={}
    for stage,model in (("before",before),("after",after)):
        answers[stage]={c["id"]:infer(model,tokenizer,c["prompt"],args.max_tokens) for c in cases}
        assessments[stage]={c["id"]:score(answers[stage][c["id"]],c) for c in cases}
    result=compare(assessments["before"],assessments["after"],cases,
                   args.max_forgetting,args.min_new_accuracy)
    result["answers"]=answers
    from response_quality_gate_v0633 import gate_quality_report
    quality = gate_quality_report(result,cases)
    result["response_quality_v0633"]=quality
    result["legacy_keyword_gate_pass"]=result["pass"]
    result["pass"]=bool(result["pass"] and quality["pass"])
    result["device"]=str(device)
    result["before_checkpoint"]=args.before
    result["after_checkpoint"]=args.after
    dest=Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"pass":result["pass"],"forgetting_rate":result["forgetting_rate"],
                      "new_accuracy":result["new_accuracy"],"output":str(dest)},ensure_ascii=False))
    raise SystemExit(0 if result["pass"] else 2)
if __name__=="__main__":main()
