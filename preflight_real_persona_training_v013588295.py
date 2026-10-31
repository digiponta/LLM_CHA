"""Preflight for a persona-chat pilot; refuses training unless explicit reviews pass.

No model is modified. No data content is printed.
"""
import argparse,json,hashlib
from pathlib import Path
from prepare_real_persona_pilot_v013588293 import norm,holdout_strings

def preflight(dataset,review,holdout,base,output,state,max_pairs=5000):
    data=Path(dataset);rev=Path(review);base=Path(base)
    dsts=[Path(output).resolve(),Path(state).resolve()]
    errors=[]
    if not data.is_file():errors.append("PILOT_FILE_MISSING")
    if not rev.is_file():errors.append("REVIEW_FILE_MISSING")
    if not base.is_file():errors.append("BASE_MODEL_MISSING")
    if len(set(dsts))<2 or base.resolve() in dsts:errors.append("PATH_COLLISION")
    if any(p.exists() for p in dsts):errors.append("OUTPUT_ALREADY_EXISTS")
    records=[];seen=set()
    blocked=holdout_strings(holdout)
    if data.is_file():
        for n,line in enumerate(data.read_text(encoding="utf-8-sig").splitlines(),1):
            if not line.strip():continue
            try:
                x=json.loads(line)
                user=x["user"].strip();answer=x["assistant"].strip()
                if x.get("source")!="chat-manual" or not user or not answer:raise ValueError()
                pair=(norm(user),norm(answer))
                if pair[0] in blocked or pair[1] in blocked:errors.append("HOLDOUT_OVERLAP")
                if pair in seen:errors.append("DUPLICATE_PAIR")
                seen.add(pair);records.append(x)
            except (ValueError,KeyError,AttributeError,TypeError):errors.append("MALFORMED_ROW_"+str(n))
        if not (1<=len(records)<=max_pairs):errors.append("PAIR_COUNT_OUT_OF_RANGE")
    approvals={}
    if rev.is_file():
        try:approvals=json.loads(rev.read_text(encoding="utf-8-sig"))
        except ValueError:errors.append("REVIEW_JSON_INVALID")
    required=("license_checked","privacy_sample_reviewed","persona_separation_approved","quality_sample_approved")
    for key in required:
        if approvals.get(key) is not True:errors.append("REVIEW_REQUIRED_"+key.upper())
    expected=approvals.get("dataset_sha256")
    actual=hashlib.sha256(data.read_bytes()).hexdigest() if data.is_file() else None
    if expected!=actual:errors.append("DATASET_HASH_MISMATCH")
    return {"status":"READY" if not errors else "BLOCKED","pair_count":len(records),
            "errors":sorted(set(errors)),"dataset_sha256":actual,
            "license_checked_by_user":approvals.get("license_checked") is True,
            "automatic_persona_identity_verification":False,
            "automatic_privacy_certification":False,"training_started":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--dataset",default="data/real_persona_pilot_v013588293.jsonl")
    p.add_argument("--review",default="results/real_persona_training_review_v013588295.json")
    p.add_argument("--holdout",default="data/daily_conversation_eval_v013588283.json")
    p.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--output-model",default="model/real-persona-cp-pilot-v013588295.pt")
    p.add_argument("--state",default="results/real-persona-cp-state-v013588295.json")
    p.add_argument("--report",default="results/real_persona_preflight_v013588295.json")
    a=p.parse_args()
    result=preflight(a.dataset,a.review,a.holdout,a.base,a.output_model,a.state)
    out=Path(a.report);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if result["status"]!="READY":raise SystemExit(2)
if __name__=="__main__":main()
