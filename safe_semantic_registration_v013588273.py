"""Fail-closed registration of human-reviewed senses into atomic/unified semantic memory.

Requires explicit existing store paths and explicit --commit. No implicit empty stores.
"""
import argparse,json,os,tempfile
from pathlib import Path
from semantic_proposition_v1090 import Proposition,load_propositions,merge_propositions
from unified_semantic_bridge_v1090 import load_unified_rows,sync_subject_from_propositions
from subject_keyed_proposition_v1090 import load_subject_index
from typed_subject_proposition_v10100 import load_typed_index
from truth_state_v10103 import load_truth_records
from sense_semantic_compatibility_v013588271 import normalized

STORES=("atomic","subject_index","typed_index","unified","truth")
BLOCKED={"REJECTED","DISPUTED","FALSE","REVOKED"}

def store_status(paths):
    result={}
    for name in STORES:
        p=Path(paths[name])
        if not p.is_file():
            result[name]={"status":"SOURCE_NOT_FOUND","count":None,"path":str(p)}
            continue
        reader={"atomic":load_propositions,"subject_index":load_subject_index,
                "typed_index":load_typed_index,"unified":load_unified_rows,
                "truth":load_truth_records}[name]
        try:
            records=reader(p)
            result[name]={"status":"SOURCE_PRESENT","count":len(records),"path":str(p)}
        except (ValueError,OSError,UnicodeError) as exc:
            result[name]={"status":"SOURCE_UNREADABLE","count":None,"path":str(p),"error":str(exc)}
    return result

def plan(quality,reviews,paths):
    states=store_status(paths)
    missing=[name for name,info in states.items() if info["status"]!="SOURCE_PRESENT"]
    entries=[]
    for c in quality.get("candidates",[]):
        cid=c.get("id")
        review=reviews.get(cid,{})
        reasons=[]
        if missing:reasons.append("MISSING_OR_UNREADABLE_STORE")
        if c.get("quality_gate")!="PASS":reasons.append("QUALITY_NOT_PASSED")
        if c.get("review_status")!="PENDING_HUMAN_REVIEW":reasons.append("UNRESOLVED_CANDIDATE_FLAG")
        if not c.get("source_url") or not c.get("evidence_sentence"):reasons.append("MISSING_PROVENANCE")
        if (review.get("decision")!="APPROVE" or not review.get("human_review_recorded")
            or not review.get("reviewer") or not review.get("note")):reasons.append("HUMAN_APPROVAL_REQUIRED")
        for field in ("subject","meaning","evidence_sentence","source_url"):
            if review.get(field)!=c.get(field):reasons.append("STALE_OR_UNBOUND_REVIEW");break
        if not missing:
            subject=normalized(c.get("subject"))
            for key,rows in (
                ("atomic",[{"subject":x.subject,"value":x.value} for x in load_propositions(Path(paths["atomic"]))]),
                ("subject_index",[{"subject":x.subject,"value":x.value} for x in load_subject_index(Path(paths["subject_index"]))]),
                ("typed_index",[{"subject":x.subject,"value":x.value} for x in load_typed_index(Path(paths["typed_index"]))]),
                ("unified",[{"subject":x.get("concept"),"value":x.get("assistant")} for x in load_unified_rows(Path(paths["unified"]))])):
                if any(normalized(x["subject"])==subject for x in rows):
                    reasons.append("EXISTING_SUBJECT_REQUIRES_MERGE_REVIEW_"+key.upper())
            if any(normalized(x.concept)==subject and x.state in BLOCKED for x in load_truth_records(Path(paths["truth"]))):
                reasons.append("TRUTH_STATE_BLOCKED")
        entries.append({"candidate_id":cid,"subject":c.get("subject"),"reasons":sorted(set(reasons)),
                        "ready":not reasons})
    return {"status":"SEMANTIC_IMPORT_READINESS","stores":states,"entries":entries,
            "ready_count":sum(x["ready"] for x in entries),"production_changed":False}

def atomic_write_bytes(path,data):
    fd,tmp=tempfile.mkstemp(prefix=".sense-",dir=str(path.parent))
    try:
        with os.fdopen(fd,"wb") as f:
            f.write(data);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def register(quality,reviews,paths,provenance_path,commit=False):
    report=plan(quality,reviews,paths)
    if not commit:return report
    if not report["entries"] or report["ready_count"]!=len(report["entries"]):
        raise ValueError("IMPORT_BLOCKED_CHECK_READINESS")
    targets=[Path(paths["atomic"]),Path(paths["unified"]),Path(provenance_path)]
    if not targets[2].is_file():raise ValueError("PROVENANCE_STORE_NOT_FOUND")
    if targets[0].resolve()==targets[1].resolve() or targets[2].resolve() in (targets[0].resolve(),targets[1].resolve()):
        raise ValueError("OVERLAPPING_STORE_PATHS")
    originals={p:p.read_bytes() for p in targets}
    try:
        old=load_propositions(targets[0])
        new=merge_propositions(old,[Proposition(c["subject"],c["meaning"]) for c in quality["candidates"]])
        payload="".join(json.dumps({"subject":x.subject,"value":x.value},ensure_ascii=False)+"\n" for x in new).encode("utf-8")
        atomic_write_bytes(targets[0],payload)
        for c in quality["candidates"]:
            if sync_subject_from_propositions(targets[0],targets[1],c["subject"]) is None:
                raise RuntimeError("UNIFIED_SYNC_FAILED")
        audit=json.loads(originals[targets[2]].decode("utf-8-sig"))
        if not isinstance(audit,list):raise ValueError("PROVENANCE_STORE_NOT_LIST")
        for c in quality["candidates"]:
            if any(x.get("candidate_id")==c["id"] for x in audit):
                raise ValueError("ALREADY_REGISTERED")
            audit.append({"candidate_id":c["id"],"subject":c["subject"],"meaning":c["meaning"],
                          "evidence_sentence":c["evidence_sentence"],"source_url":c["source_url"],
                          "reviewer":reviews[c["id"]]["reviewer"],"review_note":reviews[c["id"]]["note"],
                          "source_trust":"EXTERNAL_UNVERIFIED","human_approved":True,
                          "truth_verified":False,"model_learned":False})
        atomic_write_bytes(targets[2],(json.dumps(audit,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
    except Exception:
        for p,original in originals.items():
            atomic_write_bytes(p,original)
        raise
    report["production_changed"]=True
    report["status"]="SEMANTIC_MEMORY_REGISTERED"
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--quality",required=True);p.add_argument("--reviews",required=True)
    for name in STORES:p.add_argument("--"+name.replace("_","-"),required=True)
    p.add_argument("--provenance",required=True)
    p.add_argument("--commit",action="store_true")
    p.add_argument("--output",default="results/sense_import_readiness_v013588273.json")
    args=p.parse_args()
    paths={name:getattr(args,name) for name in STORES}
    quality=json.loads(Path(args.quality).read_text(encoding="utf-8-sig"))
    reviews=json.loads(Path(args.reviews).read_text(encoding="utf-8-sig"))
    result=register(quality,reviews,paths,args.provenance,commit=args.commit)
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"ready":result["ready_count"],
                      "total":len(result["entries"]),"production_changed":result["production_changed"],
                      "report":str(out)},ensure_ascii=False))
if __name__=="__main__":main()
