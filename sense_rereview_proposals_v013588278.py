"""Append-only AI re-review proposal ledger, never silent approval promotion.

Only an independent, source-bound assessment may recommend revision. Existing
review JSON and production memory remain unchanged until separately accepted.
"""
import argparse,hashlib,json
from pathlib import Path

def canonical(x):
    return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
def proposal(quality,review,decisions):
    candidates={c["id"]:c for c in quality.get("candidates",[])}
    original={r["candidate_id"]:r for r in review.get("records",[])}
    entries=[]
    for id,decision in decisions.items():
        c=candidates.get(id);old=original.get(id)
        if not c or not old:raise ValueError("UNKNOWN_CANDIDATE")
        if old.get("decision") not in ("DEFER","RECOMMEND_APPROVE_WITH_CAUTION"):
            raise ValueError("NOT_A_PENDING_REVIEW")
        for field in ("subject","meaning","evidence_sentence","source_url"):
            if c.get(field)!=old.get(field):raise ValueError("SOURCE_BINDING_CHANGED")
        note=str(decision.get("note","")).strip()
        if not note:raise ValueError("JUSTIFICATION_REQUIRED")
        requested=decision.get("decision")
        if requested not in ("DEFER","RECOMMEND_APPROVE_WITH_CAUTION","RECOMMEND_APPROVE"):
            raise ValueError("INVALID_REVIEW_DECISION")
        # A recommendation to promote is still only a proposal; it may not update the review.
        record={"candidate_id":id,"previous_decision":old["decision"],
                "proposed_decision":requested,"note":note,
                "candidate_fingerprint":hashlib.sha256(canonical(c)).hexdigest(),
                "reviewer_type":"AI_DELEGATE","status":"PENDING_SEPARATE_ACCEPTANCE",
                "production_changed":False}
        entries.append(record)
    return {"status":"AI_REREVIEW_PROPOSALS","entries":entries,
            "review_modified":False,"production_changed":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--quality",default="results/sense_definition_quality_v013588270.json")
    p.add_argument("--ai-review",default="results/sense_ai_delegated_review_v013588275.json")
    p.add_argument("--decisions",required=True,help="JSON dict of candidate ID -> {decision,note}")
    p.add_argument("--output",default="results/sense_rereview_proposals_v013588278.json")
    a=p.parse_args()
    def load(s):return json.loads(Path(s).read_text(encoding="utf-8-sig"))
    result=proposal(load(a.quality),load(a.ai_review),load(a.decisions))
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"proposal_count":len(result["entries"]),
                      "production_changed":False,"output":str(out)},ensure_ascii=False))
if __name__=="__main__":main()
