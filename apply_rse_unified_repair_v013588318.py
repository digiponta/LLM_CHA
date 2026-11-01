"""Apply reviewed atomic-backed Unified repairs with backup and precondition checks.

Default is dry run. Explicit --apply and --approve-concept are required.
This tool only updates the local Unified store; it never touches atomic records.
"""
import argparse,hashlib,json,os,shutil,tempfile
from pathlib import Path
from propose_rse_unified_repair_v013588317 import propose
from rse_real_memory_readonly_v013588314 import jsonl

def sha(data):return hashlib.sha256(data).hexdigest()

def repair(atomic,unified,proposal_path,apply=False,approve_concept=None):
    target=Path(unified)
    original=target.read_bytes()
    parsed=jsonl(target)
    proposal=json.loads(Path(proposal_path).read_text(encoding="utf-8-sig"))
    if proposal.get("status")!="DRY_RUN_ONLY" or proposal.get("source_files_modified") is not False:
        raise ValueError("INVALID_PROPOSAL")
    expected=propose(atomic,unified)
    if proposal.get("changes")!=expected["changes"] or proposal.get("total_unified_rows")!=len(parsed):
        raise ValueError("STALE_OR_MODIFIED_PROPOSAL")
    changes=proposal["changes"]
    if len(changes)!=1:
        raise ValueError("REQUIRES_EXACTLY_ONE_REPAIR")
    ch=changes[0]
    idx=ch["row_index"]
    if not isinstance(idx,int) or idx<0 or idx>=len(parsed):
        raise ValueError("BAD_INDEX")
    row=parsed[idx]
    if row.get("concept")!=ch["concept"] or row.get("assistant")!=ch["before"]:
        raise ValueError("ROW_PRECONDITION_FAILED")
    if any(key not in ch for key in ("before","proposed","concept")):
        raise ValueError("INVALID_CHANGE")
    result={"status":"DRY_RUN","concept":ch["concept"],"row_index":idx,
            "before":ch["before"],"after":ch["proposed"],
            "unified_sha256_before":sha(original),"source_rows":len(parsed),
            "applied":False,"backup":None}
    if not apply:return result
    if approve_concept!=ch["concept"]:
        raise ValueError("EXPLICIT_CONCEPT_APPROVAL_REQUIRED")
    backup=target.with_name(target.name+".backup-v013588318-"+sha(original)[:12])
    if backup.exists():
        if backup.read_bytes()!=original:raise ValueError("BACKUP_COLLISION")
    else:
        with backup.open("xb") as f:
            f.write(original);f.flush();os.fsync(f.fileno())
    updated=[dict(x) for x in parsed]
    updated[idx]["assistant"]=ch["proposed"]
    # Serialize without rewriting any other field; retain row count and order.
    new_data=("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in updated)).encode("utf-8")
    if sha(target.read_bytes())!=sha(original):raise ValueError("SOURCE_CHANGED_DURING_APPLY")
    fd,tmp=tempfile.mkstemp(prefix=".unified-repair-",dir=str(target.parent))
    try:
        with os.fdopen(fd,"wb") as f:
            f.write(new_data);f.flush();os.fsync(f.fileno())
        os.replace(tmp,target)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    verified=jsonl(target)
    if len(verified)!=len(parsed) or verified[idx]["assistant"]!=ch["proposed"] or any(
        a!=b for j,(a,b) in enumerate(zip(parsed,verified)) if j!=idx
    ) or any(verified[idx].get(k)!=v for k,v in row.items() if k!="assistant"):
        raise RuntimeError("POST_WRITE_VERIFICATION_FAILED_BACKUP_AT_"+str(backup))
    result.update(status="APPLIED_VERIFIED",applied=True,backup=str(backup),
                  unified_sha256_after=sha(target.read_bytes()))
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--atomic",default="data/semantic_propositions_v1090.jsonl")
    p.add_argument("--unified",default="data/unified_semantic_memory_v1090.jsonl")
    p.add_argument("--proposal",default="results/rse_unified_repair_proposal_v013588317.json")
    p.add_argument("--apply",action="store_true")
    p.add_argument("--approve-concept")
    a=p.parse_args()
    print(json.dumps(repair(a.atomic,a.unified,a.proposal,a.apply,a.approve_concept),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
