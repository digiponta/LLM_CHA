"""Batch review: AI evaluates individually; human approves one frozen manifest.

Commands: prepare, approve (interactive yes/no), commit (explicit).
No approval can be inferred from AI reviews. No concurrent writers permitted.
"""
import argparse,hashlib,json,os,sys
from pathlib import Path
from safe_semantic_registration_v013588273 import STORES,store_status,atomic_write_bytes,BLOCKED
from semantic_proposition_v1090 import load_propositions,Proposition,merge_propositions
from subject_keyed_proposition_v1090 import load_subject_index,sync_subject_index
from typed_subject_proposition_v10100 import load_typed_index,sync_typed_index
from unified_semantic_bridge_v1090 import load_unified_rows,sync_subject_from_propositions
from truth_state_v10103 import load_truth_records
from sense_semantic_compatibility_v013588271 import normalized

def canonical(obj):return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
def digest(obj):return hashlib.sha256(canonical(obj)).hexdigest()
def file_digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def json_read(path):return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def manifest(quality,ai,paths,provenance):
    states=store_status(paths)
    errors=[]
    if any(x["status"]!="SOURCE_PRESENT" for x in states.values()):errors.append("STORE_NOT_PRESENT")
    allpaths=[Path(x).resolve() for x in list(paths.values())+[provenance]]
    if len(set(allpaths))!=len(allpaths):errors.append("OVERLAPPING_PATHS")
    if not Path(provenance).is_file():errors.append("PROVENANCE_MISSING")
    else:
        try:
            audit=json_read(provenance)
            if not isinstance(audit,list):raise ValueError("not list")
        except (ValueError,UnicodeError):
            audit=[];errors.append("PROVENANCE_INVALID")
    if errors:return {"status":"BLOCKED","errors":errors,"items":[]}
    atomic=load_propositions(Path(paths["atomic"]))
    subject=load_subject_index(Path(paths["subject_index"]))
    typed=load_typed_index(Path(paths["typed_index"]))
    unified=load_unified_rows(Path(paths["unified"]))
    truths=load_truth_records(Path(paths["truth"]))
    known={normalized(x.subject) for x in atomic+subject+typed}
    known.update(normalized(x.get("concept")) for x in unified)
    done={x.get("candidate_id") for x in audit}
    reviews={}
    for row in ai.get("records",[]):
        reviews.setdefault(row.get("candidate_id"),[]).append(row)
    items=[]
    for c in quality.get("candidates",[]):
        cid=c.get("id");rr=reviews.get(cid,[])
        reasons=[]
        if len(rr)!=1:reasons.append("AI_REVIEW_MISSING_OR_DUPLICATED")
        else:
            rv=rr[0]
            if rv.get("decision")!="RECOMMEND_APPROVE":reasons.append("NOT_CLEAR_AI_RECOMMENDATION")
            if rv.get("reviewer_type")!="AI_DELEGATE" or rv.get("human_review_recorded") is not False:
                reasons.append("REVIEWER_PROVENANCE_INVALID")
            for field in ("subject","meaning","evidence_sentence","source_url"):
                if not c.get(field) or c[field]!=rv.get(field):
                    reasons.append("AI_REVIEW_NOT_BOUND_TO_CANDIDATE");break
        if c.get("quality_gate")!="PASS" or c.get("review_status")!="PENDING_HUMAN_REVIEW":
            reasons.append("QUALITY_NOT_PASSED")
        if c.get("source_trust")!="EXTERNAL_UNVERIFIED":reasons.append("SOURCE_TRUST_CHANGED")
        sub=normalized(c.get("subject"))
        if sub in known:reasons.append("EXISTING_SUBJECT")
        if cid in done:reasons.append("ALREADY_REGISTERED")
        if any(normalized(t.concept)==sub and t.state in BLOCKED for t in truths):
            reasons.append("TRUTH_BLOCKED")
        items.append({"id":cid,"subject":c.get("subject"),"meaning":c.get("meaning"),
                      "evidence_sentence":c.get("evidence_sentence"),"source_url":c.get("source_url"),
                      "reviewer_type":"AI_DELEGATE",
                      "ai_decision":rr[0].get("decision") if len(rr)==1 else "MISSING",
                      "ai_note":rr[0].get("note","") if len(rr)==1 else "",
                      "eligible":not reasons,"reasons":sorted(set(reasons))})
    eligible=[x for x in items if x["eligible"]]
    fingerprints={k:file_digest(v) for k,v in paths.items()}
    fingerprints["provenance"]=file_digest(provenance)
    payload={"items":eligible,"stores":fingerprints}
    return {"status":"BATCH_PREPARED","items":items,"eligible":eligible,
            "eligible_count":len(eligible),"blocked_count":len(items)-len(eligible),
            "snapshot":fingerprints,"batch_hash":digest(payload),"production_changed":False}

def approve(manifest_data,decision):
    if manifest_data.get("status")!="BATCH_PREPARED" or not manifest_data.get("eligible"):
        raise ValueError("NO_ELIGIBLE_BATCH")
    if decision not in ("yes","no"):raise ValueError("ANSWER_MUST_BE_YES_OR_NO")
    return {"status":"BATCH_APPROVED" if decision=="yes" else "BATCH_REJECTED",
            "batch_hash":manifest_data["batch_hash"],
            "approved_candidate_ids":[x["id"] for x in manifest_data["eligible"]] if decision=="yes" else [],
            "approval_type":"HUMAN_BATCH_DECISION","human_answer":decision,
            "production_changed":False}

def commit(manifest_data,approval,quality,ai,paths,provenance):
    if approval.get("status")!="BATCH_APPROVED" or approval.get("human_answer")!="yes":
        raise ValueError("HUMAN_BATCH_APPROVAL_REQUIRED")
    current=manifest(quality,ai,paths,provenance)
    if current.get("status")!="BATCH_PREPARED" or not current["eligible"]:
        raise ValueError("FRESH_PREFLIGHT_FAILED")
    if current["batch_hash"]!=manifest_data.get("batch_hash") or current["batch_hash"]!=approval.get("batch_hash"):
        raise ValueError("BATCH_OR_STORE_CHANGED_REAPPROVAL_REQUIRED")
    if [x["id"] for x in current["eligible"]]!=approval.get("approved_candidate_ids"):
        raise ValueError("APPROVAL_SCOPE_MISMATCH")
    # File backups allow rollback on ordinary Python exceptions, not power loss.
    targets=[Path(paths[k]) for k in STORES]+[Path(provenance)]
    original={p:p.read_bytes() for p in targets}
    try:
        old=load_propositions(Path(paths["atomic"]))
        new=merge_propositions(old,[Proposition(x["subject"],x["meaning"]) for x in current["eligible"]])
        text="".join(json.dumps({"subject":x.subject,"value":x.value},ensure_ascii=False)+"\n" for x in new)
        atomic_write_bytes(Path(paths["atomic"]),text.encode("utf-8"))
        # Derived indexes follow the actual atomic store; do not overwrite existing unified records.
        sync_subject_index(Path(paths["atomic"]),Path(paths["subject_index"]))
        sync_typed_index(Path(paths["atomic"]),Path(paths["typed_index"]))
        for item in current["eligible"]:
            if sync_subject_from_propositions(Path(paths["atomic"]),Path(paths["unified"]),item["subject"]) is None:
                raise RuntimeError("UNIFIED_SYNC_FAILED")
        audit=json.loads(original[Path(provenance)].decode("utf-8-sig"))
        for item in current["eligible"]:
            audit.append({"candidate_id":item["id"],"subject":item["subject"],
                          "meaning":item["meaning"],"evidence_sentence":item["evidence_sentence"],
                          "source_url":item["source_url"],"source_trust":"EXTERNAL_UNVERIFIED",
                          "ai_review_type":"AI_DELEGATE","ai_note":item["ai_note"],
                          "batch_hash":current["batch_hash"],"human_batch_approved":True,
                          "human_reviewed_each":False,"truth_verified":False,"model_learned":False})
        atomic_write_bytes(Path(provenance),(json.dumps(audit,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
    except Exception:
        for p,data in original.items():atomic_write_bytes(p,data)
        raise
    return {"status":"BATCH_REGISTERED","batch_hash":current["batch_hash"],
            "registered_count":len(current["eligible"]),"production_changed":True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=["prepare","approve","commit"])
    p.add_argument("--quality",default="results/sense_definition_quality_v013588270.json")
    p.add_argument("--ai-review",default="results/sense_ai_delegated_review_v013588275.json")
    for k in STORES:p.add_argument("--"+k.replace("_","-"),required=True)
    p.add_argument("--provenance",required=True)
    p.add_argument("--manifest",default="results/sense_batch_manifest_v013588277.json")
    p.add_argument("--approval",default="results/sense_batch_approval_v013588277.json")
    a=p.parse_args();paths={k:getattr(a,k) for k in STORES}
    if a.action=="prepare":
        result=manifest(json_read(a.quality),json_read(a.ai_review),paths,a.provenance)
        Path(a.manifest).parent.mkdir(parents=True,exist_ok=True)
        Path(a.manifest).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    elif a.action=="approve":
        m=json_read(a.manifest)
        print(json.dumps({"batch_hash":m.get("batch_hash"),"eligible":m.get("eligible"),
                          "excluded":[x for x in m.get("items",[]) if not x["eligible"]]},ensure_ascii=False,indent=2))
        if not m.get("eligible"):
            result={"status":"EMPTY_BATCH_SKIPPED","batch_hash":m.get("batch_hash"),"eligible_count":0,"production_changed":False}
        else:
            answer=input("Approve exactly these eligible entries? [yes/no]: ").strip().lower()
            result=approve(m,answer)
        Path(a.approval).parent.mkdir(parents=True,exist_ok=True)
        Path(a.approval).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    else:
        result=commit(json_read(a.manifest),json_read(a.approval),json_read(a.quality),
                      json_read(a.ai_review),paths,a.provenance)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
