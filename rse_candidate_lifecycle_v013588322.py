"""Explicit RSE candidate approval lifecycle. No chat.py integration.

Immutable candidate question/answer fingerprints guard against approval reuse.
APPROVED is an operator review state, not verification of factual truth.
"""
import argparse,hashlib,json,os
from pathlib import Path
from rse_semantic_theme_v013588312 import select,semantic_features
from rse_adoption_policy_v013588321 import decide

def fingerprint(question,answer):
    return hashlib.sha256(json.dumps([question,answer],ensure_ascii=False,separators=(",",":")).encode("utf-8")).hexdigest()

def read(path):
    p=Path(path)
    if not p.exists():return {"schema":"rse-candidate-lifecycle-v1","records":[]}
    data=json.loads(p.read_text(encoding="utf-8-sig"))
    if data.get("schema")!="rse-candidate-lifecycle-v1" or not isinstance(data.get("records"),list):
        raise ValueError("INVALID_LIFECYCLE_STORE")
    return data

def save(path,data):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_name(p.name+".tmp")
    if tmp.exists():raise ValueError("TEMP_FILE_EXISTS")
    with tmp.open("x",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2);f.write("\n");f.flush();os.fsync(f.fileno())
    os.replace(tmp,p)

def register(store,candidate_id,question,answer,source):
    if not candidate_id or not question.strip() or not answer.strip() or not source.strip():raise ValueError("FIELDS_REQUIRED")
    data=read(store)
    if any(x["id"]==candidate_id for x in data["records"]):raise ValueError("ID_ALREADY_REGISTERED")
    feature=semantic_features(question)
    rec={"id":candidate_id,"question":question,"answer":answer,"source":source,
         "theme":feature["theme"],"intent":feature["intent"],"time":feature["time"],
         "fingerprint":fingerprint(question,answer),"state":"PENDING","reviewer":None}
    data["records"].append(rec);save(store,data)
    return rec

def review(store,candidate_id,state,reviewer):
    if state not in {"APPROVED","REVOKED"}:raise ValueError("BAD_STATE")
    if not reviewer.strip():raise ValueError("REVIEWER_REQUIRED")
    data=read(store)
    matches=[x for x in data["records"] if x["id"]==candidate_id]
    if len(matches)!=1:raise ValueError("ID_NOT_UNIQUE_OR_MISSING")
    rec=matches[0]
    if fingerprint(rec["question"],rec["answer"])!=rec["fingerprint"]:raise ValueError("CONTENT_CHANGED")
    if state=="APPROVED" and rec["state"]!="PENDING":raise ValueError("APPROVAL_REQUIRES_PENDING")
    if state=="REVOKED" and rec["state"]!="APPROVED":raise ValueError("REVOCATION_REQUIRES_APPROVED")
    rec["state"]=state;rec["reviewer"]=reviewer
    save(store,data)
    return rec

def resolve(store,query,observed_answer=None,observed_route=""):
    records=read(store)["records"]
    eligible=[r for r in records if r["state"]=="APPROVED" and
              fingerprint(r["question"],r["answer"])==r["fingerprint"]]
    result=select(query,eligible)
    selected=result.get("candidate_id")
    matches=[r for r in eligible if r["id"]==selected] if selected is not None else []
    authorized=len(matches)==1 and result["status"]=="ANSWER_SELECTED"
    decision=decide(observed_answer=observed_answer,observed_route=observed_route,
                    rse_status=result["status"],rse_answer=result["answer"],
                    rse_approved=authorized)
    return {"query":query,"rse":result,"eligible_count":len(eligible),
            "candidate_approved":authorized,"decision":decision.__dict__,
            "live_integration":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--store",default="data/rse_candidate_lifecycle_v013588322.json")
    sub=p.add_subparsers(dest="command",required=True)
    a=sub.add_parser("register");a.add_argument("--id",required=True);a.add_argument("--question",required=True);a.add_argument("--answer",required=True);a.add_argument("--source",required=True)
    v=sub.add_parser("approve");v.add_argument("--id",required=True);v.add_argument("--reviewer",required=True)
    v=sub.add_parser("revoke");v.add_argument("--id",required=True);v.add_argument("--reviewer",required=True)
    q=sub.add_parser("resolve");q.add_argument("--query",required=True);q.add_argument("--observed-answer");q.add_argument("--observed-route",default="")
    sub.add_parser("list")
    args=p.parse_args()
    if args.command=="register":out=register(args.store,args.id,args.question,args.answer,args.source)
    elif args.command in ("approve","revoke"):out=review(args.store,args.id,"APPROVED" if args.command=="approve" else "REVOKED",args.reviewer)
    elif args.command=="resolve":out=resolve(args.store,args.query,args.observed_answer,args.observed_route)
    else:out=read(args.store)
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
