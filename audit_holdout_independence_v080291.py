"""v0.8.0.29.1: distinguish manually resolved overlap from unresolved warnings.

Read-only: does not attest corpus independence or approve a formal holdout.
"""
import argparse
import json
from pathlib import Path
from audit_holdout_independence_v08028 import review as base_review

def review(source,store,manual_review=None,lexical_threshold=0.80):
    result=base_review(source,store,manual_review,lexical_threshold)
    if result.get("status") not in ("REVIEW_REQUIRED","MANUAL_REVIEW_RECORDED"):
        return result
    reviews={}
    if manual_review is not None:
        path=Path(manual_review)
        if not path.is_file():
            result["status"]="REVIEW_REQUIRED"
            result["review_error"]="REVIEW_FILE_NOT_FOUND"
            return result
        try:
            raw=json.loads(path.read_text(encoding="utf-8-sig"))
            if not isinstance(raw,dict) or not isinstance(raw.get("reviews"),list):
                raise ValueError("INVALID_REVIEW_FORMAT")
            for item in raw["reviews"]:
                if not isinstance(item,dict) or not isinstance(item.get("id"),str) or item["id"] in reviews:
                    raise ValueError("INVALID_OR_DUPLICATE_REVIEW_ID")
                reviews[item["id"]]=item
        except (OSError,UnicodeError,ValueError) as exc:
            result["status"]="REVIEW_REQUIRED"
            result["review_error"]=str(exc)
            return result
    resolved=0
    for finding in result["findings"]:
        record=reviews.get(finding.get("id"),{})
        # Manual resolution is accepted only when all three checks were
        # explicitly documented and overlap_manually_resolved is true.
        is_resolved=(finding.get("human_checks_complete") is True
                     and record.get("source_checked") is True
                     and record.get("answer_checked") is True
                     and record.get("training_nonoverlap_checked") is True
                     and record.get("overlap_manually_resolved") is True)
        finding["overlap_review_resolution"]="NOT_APPLICABLE"
        if finding.get("overlap_candidates"):
            if is_resolved:
                finding["flags"]=[f for f in finding["flags"] if f not in (
                    "POSSIBLE_SEMANTIC_OR_LEXICAL_OVERLAP","OVERLAP_REVIEW_PENDING")]
                finding["overlap_review_resolution"]="MANUALLY_RESOLVED"
                resolved+=1
            else:
                finding["overlap_review_resolution"]="PENDING"
        finding["overlap_candidates"] = finding.get("overlap_candidates",[])
    result["resolved_overlap_record_count"]=resolved
    result["status"]=("REVIEW_REQUIRED" if any(f.get("flags") for f in result["findings"])
                      else "MANUAL_REVIEW_RECORDED")
    result["semantic_independence_verified"]=False
    result["formal_holdout_approved"]=False
    result["written"]=False
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",nargs="?",default="data/holdout_review_candidates_v08026.json")
    p.add_argument("--store",default="data/unapproved_llm_candidates_v074446.json")
    p.add_argument("--review",default=None)
    p.add_argument("--threshold",type=float,default=0.80)
    a=p.parse_args()
    print(json.dumps(review(a.source,a.store,a.review,a.threshold),ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
