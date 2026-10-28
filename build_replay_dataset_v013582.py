"""v0.13.58.2 reviewed replay dataset builder.

Default --prepare exports candidate records only. No approvals are invented.
After manual review of candidate JSON, --apply emits only approved training
records and audits token counts and exact overlap against reserved validation.
"""
import argparse,hashlib,json
from pathlib import Path

def load_jsonl(path):
    rows=[]
    for no,line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(),1):
        if not line.strip():continue
        obj=json.loads(line)
        if not isinstance(obj,dict) or not isinstance(obj.get("user"),str) or not isinstance(obj.get("assistant"),str):
            raise ValueError(f"{path}:{no}: invalid dialogue pair")
        rows.append((no,obj))
    return rows

def key(u,a):return (" ".join(u.split())," ".join(a.split()))
def get_reserved(paths):
    reserved=set(); questions=set()
    for p in paths:
        for _,obj in load_jsonl(p):
            reserved.add(key(obj["user"],obj["assistant"]))
            questions.add(" ".join(obj["user"].split()))
    return reserved,questions

def candidates(sources,reserved_paths):
    reserved,questions=get_reserved(reserved_paths)
    entries=[];stats={};seen=set()
    for domain,path in sources.items():
        accepted=0;blocked=0
        for line,obj in load_jsonl(path):
            u,a=key(obj["user"],obj["assistant"])
            if not u or not a:continue
            # Block identical questions too: avoids reusing heldout prompts
            # with different responses.
            if (u,a) in reserved or u in questions:
                blocked+=1;continue
            signature=(u,a)
            if signature in seen:continue
            seen.add(signature)
            entries.append({"id":f"{domain}-{line:05d}","domain":domain,
                  "user":u,"assistant":a,"source":str(path),
                  "source_line":line,"approved":False,
                  "persona_reviewed":False,
                  "review_note":""})
            accepted+=1
        stats[domain]={"candidate_count":accepted,"blocked_by_reserved":blocked}
    return entries,stats

def audit_review(packet,source_rows,reserved_paths):
    reserved,questions=get_reserved(reserved_paths)
    verified={x["id"]:x for x in source_rows}
    if len(packet)!=len(verified):raise ValueError("review list count changed")
    seen=set();out={"conversation":[],"persona":[],"knowledge":[]}
    pending=0;rejected=0
    for row in packet:
        ident=row.get("id")
        if ident in seen or ident not in verified:raise ValueError("unknown/duplicate review id")
        seen.add(ident)
        original=verified[ident]
        for field in ("id","domain","user","assistant","source","source_line"):
            if row.get(field)!=original[field]:raise ValueError(f"tampered review payload: {ident}:{field}")
        domain=row["domain"];u=row["user"];a=row["assistant"]
        if key(u,a) in reserved or u in questions:raise ValueError("holdout collision in review")
        if type(row.get("approved")) is not bool:raise ValueError("approved must be boolean")
        if not row["approved"]:
            pending+=1 if not row.get("review_note") else 0
            rejected+=1 if row.get("review_note") else 0
            continue
        if domain=="persona" and row.get("persona_reviewed") is not True:
            raise ValueError("approved persona requires persona_reviewed=true")
        out[domain].append({"user":u,"assistant":a,"approved":True,
                            **({"persona_reviewed":True} if domain=="persona" else {})})
    if pending:raise ValueError(f"{pending} records have no review note; review required")
    return out,{"approved":sum(map(len,out.values())),"rejected":rejected,"pending":pending}

def run(args):
    sources={"conversation":args.conversation,"persona":args.persona,"knowledge":args.knowledge}
    paths=list(sources.values())+[args.validation]
    for p in paths:
        if not p.is_file():raise FileNotFoundError(p)
    if any(k in p.name.lower() for p in sources.values() for k in ("_val","holdout","test","eval")):
        raise ValueError("reserved/evaluation file used as training")
    entries,stats=candidates(sources,[args.validation])
    packet=args.packet
    if args.mode=="prepare":
        if packet.exists():raise FileExistsError(packet)
        packet.parent.mkdir(parents=True,exist_ok=True)
        packet.write_text(json.dumps({"version":"v0.13.58.2","source_sha256":{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
          "stats":stats,"records":entries},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        return {"status":"REVIEW_REQUIRED","records":len(entries),"stats":stats,"packet":str(packet)}
    obj=json.loads(packet.read_text(encoding="utf-8-sig"))
    if obj.get("version")!="v0.13.58.2" or obj.get("source_sha256")!={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}:
        raise ValueError("source hash mismatch")
    approved,review=audit_review(obj["records"],entries,[args.validation])
    if not review["approved"]:raise ValueError("no reviewed training records")
    files={name:args.output_dir/f"replay_{name}_approved_v013582.jsonl" for name in approved}
    if any(p.exists() for p in files.values()):raise FileExistsError("output exists")
    args.output_dir.mkdir(parents=True,exist_ok=True)
    for name,p in files.items():
        with p.open("x",encoding="utf-8") as f:
            for record in approved[name]:f.write(json.dumps(record,ensure_ascii=False)+"\n")
    return {"status":"APPROVED_DATA_EXPORTED","review":review,"files":{k:str(v) for k,v in files.items()},
            "foundation_missing_large_corpus":True,"training_approved":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=["prepare","apply"],default="prepare")
    p.add_argument("--conversation",type=Path,default=Path("data/nagato_chat.jsonl"))
    p.add_argument("--persona",type=Path,default=Path("data/nagato_identity_anchor.jsonl"))
    p.add_argument("--knowledge",type=Path,default=Path("data/nagato_response_completion.jsonl"))
    p.add_argument("--validation",type=Path,default=Path("data/nagato_chat_val.jsonl"))
    p.add_argument("--packet",type=Path,default=Path("results/replay_review_candidates_v013582.json"))
    p.add_argument("--output-dir",type=Path,default=Path("data"))
    args=p.parse_args()
    print(json.dumps(run(args),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
