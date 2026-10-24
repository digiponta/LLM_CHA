"""v0.8.0.28: conservative topic-overlap noise reduction.

Reuses v0.8.0.27 provenance checks and human review requirements. Only
numeric-only topic matches are suppressed; lexical similarities >= threshold
remain flagged. Not semantic entailment or independent holdout certification.
"""
import argparse
import json
import re
import unicodedata
from audit_holdout_independence_v08027 import review as original_review

GENERIC_TERMS = frozenset({"こと", "もの", "ため", "方法", "情報", "場合"})

def substantive(term):
    token = unicodedata.normalize("NFKC", str(term)).strip().casefold()
    if not token or token in GENERIC_TERMS:
        return False
    if re.fullmatch(r"[0-9０-９]+(?:[.,．，][0-9０-９]+)*", token):
        return False
    return True

def review(source, store, manual_review=None, lexical_threshold=0.80):
    result = original_review(source, store, manual_review,
                             lexical_threshold=lexical_threshold)
    if result.get("status") not in ("REVIEW_REQUIRED", "MANUAL_REVIEW_RECORDED"):
        return result
    suppressed = 0
    for row in result["findings"]:
        matches = row.get("overlap_candidates", [])
        kept = []
        excluded = []
        for match in matches:
            significant = [w for w in match["common_terms"] if substantive(w)]
            strong_lexical = match["max_lexical_similarity"] >= lexical_threshold
            adjusted = dict(match, common_terms=significant)
            if significant or strong_lexical:
                kept.append(adjusted)
            else:
                excluded.append({"candidate_id": match["candidate_id"],
                                 "reason": "NUMERIC_OR_GENERIC_TERM_ONLY"})
                suppressed += 1
        row["overlap_candidates"] = kept
        row["suppressed_noise"] = excluded
        if not kept:
            row["flags"] = [flag for flag in row["flags"] if flag not in (
                "POSSIBLE_SEMANTIC_OR_LEXICAL_OVERLAP", "OVERLAP_REVIEW_PENDING")]
        row["human_checks_complete"] = row.get("human_checks_complete", False)
    result["status"] = ("REVIEW_REQUIRED" if any(x.get("flags") for x in result["findings"])
                        else "MANUAL_REVIEW_RECORDED")
    result["suppressed_noise_matches"] = suppressed
    result["semantic_independence_verified"] = False
    result["training_exposure_excluded"] = False
    result["formal_holdout_approved"] = False
    result["written"] = False
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", nargs="?", default="data/holdout_review_candidates_v08026.json")
    p.add_argument("--store", default="data/unapproved_llm_candidates_v074446.json")
    p.add_argument("--review", default=None)
    p.add_argument("--threshold", type=float, default=0.80)
    args = p.parse_args()
    print(json.dumps(review(args.source, args.store, args.review, args.threshold),
                     ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
