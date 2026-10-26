"""LLM_CHA v0.10.1.4: offline audit, never used to select generated candidates.

Input: results/decoding_pair_audit_v01013.json
Termination is inferred from cap and incomplete text, NOT asserted to be EOS.
Exact EOS/newline reporting requires decoder instrumentation in a future version.
"""
import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

def normalize(text):
    return unicodedata.normalize("NFKC", text).strip()

def repeated_fragment(text):
    # Heuristic: adjacent repeated phrases, not a semantic judgment.
    normalized = normalize(text)
    return bool(re.search(r"(.{2,18}?)(?:\s*[,、，]\s*\1){2,}", normalized))

def assess(row):
    a = row["baseline_output"]
    b = row["challenger_output"]
    target = row["reference"]
    raw_match_a = a.strip() == target.strip()
    raw_match_b = b.strip() == target.strip()
    norm_match_a = normalize(a) == normalize(target)
    norm_match_b = normalize(b) == normalize(target)
    cap_a = bool(row["baseline_cap_hit"])
    cap_b = bool(row["challenger_cap_hit"])
    return {
        "id": row["id"],
        "paired_category": row["category"],
        "greedy_exact": raw_match_a,
        "beam3_exact": raw_match_b,
        "greedy_normalized_exact": norm_match_a,
        "beam3_normalized_exact": norm_match_b,
        "greedy_unicode_only_mismatch": not raw_match_a and norm_match_a,
        "beam3_unicode_only_mismatch": not raw_match_b and norm_match_b,
        "greedy_cap_hit": cap_a,
        "beam3_cap_hit": cap_b,
        "greedy_termination": "TOKEN_CAP_REACHED" if cap_a else "STOP_REASON_UNOBSERVED",
        "beam3_termination": "TOKEN_CAP_REACHED" if cap_b else "STOP_REASON_UNOBSERVED",
        "greedy_repetition_heuristic": repeated_fragment(a),
        "beam3_repetition_heuristic": repeated_fragment(b),
        "reference": target,
        "greedy_output": a,
        "beam3_output": b
    }

def audit(payload):
    if payload.get("protocol") != "TRAIN_ASSOCIATED_DEV_NOT_HOLDOUT":
        raise ValueError("Unknown evaluation protocol")
    rows = payload.get("records", [])
    if not rows:
        raise ValueError("Empty paired records")
    result = [assess(r) for r in rows]
    summary = {
        "cases": len(result),
        "greedy_exact": sum(r["greedy_exact"] for r in result),
        "beam3_exact": sum(r["beam3_exact"] for r in result),
        "greedy_normalized_exact": sum(r["greedy_normalized_exact"] for r in result),
        "beam3_normalized_exact": sum(r["beam3_normalized_exact"] for r in result),
        "greedy_cap_hit": sum(r["greedy_cap_hit"] for r in result),
        "beam3_cap_hit": sum(r["beam3_cap_hit"] for r in result),
        "greedy_repetition_heuristic": sum(r["greedy_repetition_heuristic"] for r in result),
        "beam3_repetition_heuristic": sum(r["beam3_repetition_heuristic"] for r in result),
        "beam3_remaining_normalized_mismatch_ids": [r["id"] for r in result if not r["beam3_normalized_exact"]],
    }
    return {"protocol": payload["protocol"], "diagnostic_version": "v0.10.1.4",
            "limitations": ["NFKC is evaluation-only", "No EOS/newline distinction available in historical rows",
                            "Repetition is a heuristic; semantic contradictions/topic drift require separate review",
                            "Exact match is not factual truth"], "summary": summary, "records": result}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="results/decoding_pair_audit_v01013.json")
    p.add_argument("--output", default="results/decoding_diagnostics_v01014.json")
    a=p.parse_args()
    report=audit(json.loads(Path(a.input).read_text(encoding="utf-8-sig")))
    dest=Path(a.output)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report["summary"],ensure_ascii=False,indent=2))
    print("report:",dest)

if __name__=="__main__":
    main()
