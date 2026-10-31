"""Explicit delegated-AI approval for ONE frozen candidate, with fail-closed commit.

Never impersonates human review. Refuses unreviewed/cautioned/held candidates,
missing stores, existing subject, blocked Truth State and stale review evidence.
"""
import argparse,hashlib,json
from pathlib import Path
from safe_semantic_registration_v013588273 import STORES,store_status,BLOCKED,atomic_write_bytes
from semantic_proposition_v1090 import Proposition,load_propositions
from subject_keyed_proposition_v1090 import load_subject_index
from typed_subject_proposition_v10100 import load_typed_index
from unified_semantic_bridge_v1090 import load_unified_rows,sync_subject_from_propositions
from truth_state_v10103 import load_truth_records
from sense_semantic_compatibility_v013588271 import normalized

ALLOWED_ID="sense-ab912703fcc269a1"
AUTHORIZATION="I_DELEGATE_AI_REVIEW_FOR_SPHALERITE_V013588276"
def inspect(quality,ai_review,paths,provenance_path,authorization):
    statuses=store_status(paths)
    reasons=[]
    if authorization!=AUTHORIZATION:reasons.append("EXPLICIT_DELEGATION_REQUIRED")
    if any(x["status"]!="SOURCE_PRESENT" for x in statuses.values()):reasons.append("STORE_MISSING_OR_INVALID")
    paths_all=[Path(v).resolve() for v in paths.values()]+[Path(provenance_path).resolve()]
    if len(set(paths_all))!=len(paths_all):reasons.append("OVERLAPPING_STORE_PATHS")
    candidates=quality.get("candidates",[])
    selected=[c for c in candidates if c.get("id")==ALLOWED_ID]
    records=[x for x in ai_review.get("records",[]) if x.get("candidate_id")==ALLOWED_ID]
    if len(selected)!=1 or len(records)!=1:
        reasons.append("CANDIDATE_OR_REVIEW_NOT_UNIQUE")
    else:
        c,review=selected[0],records[0]
        if c.get("subject")!="閃亜鉛鉱" or c.get("quality_gate")!="PASS" or c.get("review_status")!="PENDING_HUMAN_REVIEW":
            reasons.append("UNQUALIFIED_CANDIDATE")
        for key in ("subject","meaning","evidence_sentence","source_url"):
            if not c.get(key) or c.get(key)!=review.get(key):
                reasons.append("REVIEW_EVIDENCE_MISMATCH")
                break
        if (review.get("decision")!="RECOMMEND_APPROVE" or review.get("reviewer_type")!="AI_DELEGATE"
            or review.get("human_review_recorded") is not False or not review.get("note")):
            reasons.append("DELEGATED_REVIEW_NOT_ELIGIBLE")
        if c.get("source_trust")!="EXTERNAL_UNVERIFIED":
            reasons.append("SOURCE_TRUST_CHANGED")
        if not any(x.get("id")==ALLOWED_ID and x.get("new_id")==ALLOWED_ID and x.get("review_transfer_allowed") is False for x in quality.get("id_migrations",[])):
            reasons.append("CANDIDATE_MIGRATION_NOT_VERIFIED")
        if not any(x.get("source_url","").startswith("https://ja.wikipedia.org/wiki/") for x in [c]):
            reasons.append("SOURCE_NOT_ALLOWLISTED")
        if all(x["status"]=="SOURCE_PRESENT" for x in statuses.values()):
            subject=normalized(c["subject"])
            pools={
                "atomic":[x.subject for x in load_propositions(Path(paths["atomic"]))],
                "subject_index":[x.subject for x in load_subject_index(Path(paths["subject_index"]))],
                "typed_index":[x.subject for x in load_typed_index(Path(paths["typed_index"]))],
                "unified":[x.get("concept") for x in load_unified_rows(Path(paths["unified"]))]
            }
            if any(normalized(x)==subject for v in pools.values() for x in v):
                reasons.append("SUBJECT_ALREADY_PRESENT")
            if any(normalized(x.concept)==subject and x.state in BLOCKED for x in load_truth_records(Path(paths["truth"]))):
                reasons.append("TRUTH_BLOCKED")
    p=Path(provenance_path)
    if not p.is_file():reasons.append("PROVENANCE_NOT_FOUND")
    else:
        try:
            audit=json.loads(p.read_text(encoding="utf-8-sig"))
            if not isinstance(audit,list):raise ValueError("not list")
            if any(x.get("candidate_id")==ALLOWED_ID for x in audit):
                reasons.append("ALREADY_REGISTERED")
        except (ValueError,UnicodeError):reasons.append("PROVENANCE_INVALID")
    return {"status":"DELEGATED_IMPORT_READY" if not reasons else "DELEGATED_IMPORT_BLOCKED",
            "candidate_id":ALLOWED_ID,"reasons":sorted(set(reasons)),"stores":statuses,
            "ready":not reasons,"production_changed":False}

def register(quality,ai_review,paths,provenance_path,authorization,commit=False):
    report=inspect(quality,ai_review,paths,provenance_path,authorization)
    if not commit:return report
    if not report["ready"]:raise ValueError("DELEGATED_IMPORT_BLOCKED")
    c=next(c for c in quality["candidates"] if c["id"]==ALLOWED_ID)
    source=Path(paths["atomic"]); unified=Path(paths["unified"]); audit_path=Path(provenance_path)
    paths_backup=[source,unified,audit_path]
    original={p:p.read_bytes() for p in paths_backup}
    try:
        if load_propositions(source):
            raise ValueError("ATOMIC_CHANGED_RECHECK_REQUIRED")
        statement={"subject":c["subject"],"value":c["meaning"]}
        atomic_write_bytes(source,(json.dumps(statement,ensure_ascii=False)+"\n").encode("utf-8"))
        if sync_subject_from_propositions(source,unified,c["subject"]) is None:
            raise RuntimeError("UNIFIED_SYNC_FAILED")
        audit=json.loads(original[audit_path].decode("utf-8-sig"))
        if any(x.get("candidate_id")==ALLOWED_ID for x in audit):
            raise ValueError("ALREADY_REGISTERED")
        audit.append({"candidate_id":ALLOWED_ID,"subject":c["subject"],
                      "meaning":c["meaning"],"source_url":c["source_url"],
                      "evidence_sentence":c["evidence_sentence"],
                      "reviewer_type":"AI_DELEGATE","reviewer":"ChatGPT (AI delegated review)",
                      "review_decision":"RECOMMEND_APPROVE",
                      "authorization":AUTHORIZATION,"human_review_recorded":False,
                      "human_approved":False,"delegated_approved":True,
                      "truth_verified":False,"source_trust":"EXTERNAL_UNVERIFIED",
                      "model_learned":False})
        atomic_write_bytes(audit_path,(json.dumps(audit,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
    except Exception:
        for p,old in original.items():atomic_write_bytes(p,old)
        raise
    report["status"]="DELEGATED_SEMANTIC_REGISTERED";report["production_changed"]=True
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--quality",required=True);p.add_argument("--ai-review",required=True)
    for k in STORES:p.add_argument("--"+k.replace("_","-"),required=True)
    p.add_argument("--provenance",required=True)
    p.add_argument("--authorization",default="")
    p.add_argument("--commit",action="store_true")
    p.add_argument("--output",default="results/sense_delegated_import_v013588276.json")
    a=p.parse_args();paths={k:getattr(a,k) for k in STORES}
    quality=json.loads(Path(a.quality).read_text(encoding="utf-8-sig"))
    reviews=json.loads(Path(a.ai_review).read_text(encoding="utf-8-sig"))
    result=register(quality,reviews,paths,a.provenance,a.authorization,a.commit)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"ready":result["ready"],
                      "reasons":result["reasons"],"production_changed":result["production_changed"],
                      "report":str(out)},ensure_ascii=False))
if __name__=="__main__":main()
