"""v0.70 quality-filtered sense discovery; isolated, no automatic approvals."""
import hashlib
import re
from evidence_sense_discovery_v013588268 import inspect_snapshot

NON_DEFINITION=re.compile(r"歴史がある|認められるようにな|紆余曲折|論争が続|研究が進|発見された|年に提唱|と考えられていた")
DEFINITION=re.compile(r"である$|を指す$|意味する$|現象である$|理論・分野$|鉱物である$|爆発的膨張$")
PUNCT=re.compile(r"^[、，,:：\s]+")

def qualify(row):
    meaning=PUNCT.sub("",str(row.get("meaning","")).strip()).rstrip("。").strip()
    if not meaning or NON_DEFINITION.search(meaning):
        return None,"NON_DEFINITION"
    if not DEFINITION.search(meaning):
        return None,"NO_DEFINITION_PREDICATE"
    if not row.get("subject") or not row.get("evidence_sentence"):
        return None,"MISSING_SUBJECT_OR_EVIDENCE"
    new_id="sense-"+hashlib.sha256((row["subject"]+"\n"+meaning).encode("utf-8")).hexdigest()[:16]
    revised={**row,"id":new_id,"meaning":meaning,"approved":False,
             "review_status":"PENDING_HUMAN_REVIEW",
             "auto_promote":False,"quality_gate":"PASS"}
    return revised,None

def evaluate(discovery):
    accepted=[];rejected=[];migrations=[]
    for original in discovery.get("candidates",[]):
        qualified,reason=qualify(original)
        if qualified is None:
            rejected.append({"id":original["id"],"subject":original.get("subject"),"reason":reason})
            migrations.append({"old_id":original["id"],"new_id":None,"reason":reason,
                               "review_transfer_allowed":False})
            continue
        accepted.append(qualified)
        migrations.append({"old_id":original["id"],"new_id":qualified["id"],
                           "reason":"NORMALIZED" if original["id"]!=qualified["id"] else "UNCHANGED",
                           "review_transfer_allowed":False})
    return {"status":"SENSE_DEFINITION_QUALITY_DIAGNOSTIC",
            "candidate_count_before":len(discovery.get("candidates",[])),
            "candidate_count_after":len(accepted),
            "accepted":accepted,"rejected":rejected,"id_migrations":migrations,
            "candidates":accepted,"approved_count":0,"production_changed":False}

def main():
    import argparse,json
    from pathlib import Path
    p=argparse.ArgumentParser()
    p.add_argument("--source",default="results/sense_discovery_v013588268_fixed.json")
    p.add_argument("--output",default="results/sense_definition_quality_v013588270.json")
    a=p.parse_args()
    report=evaluate(json.loads(Path(a.source).read_text(encoding="utf-8-sig")))
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"before":report["candidate_count_before"],
                      "after":report["candidate_count_after"],"rejected":len(report["rejected"]),
                      "approved":0,"report":str(out)},ensure_ascii=False))
if __name__=="__main__":main()
