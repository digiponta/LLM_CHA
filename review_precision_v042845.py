#!/usr/bin/env python3
"""LLM_CHA v0.4.28.45: deterministic review sampling & conservative precision report."""
import argparse
import hashlib
import json
import math
from pathlib import Path

VERSION = "v0.4.28.45"
DIMENSIONS = ("relevance", "semantic_consistency", "context_independence", "factual_correctness", "training_suitability")
VALID = ("pass", "fail", "unknown")

def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()

def validate_audit(data):
    if data.get("version") != "v0.4.28.44" or data.get("mode") != "CONTEXT_QA_HEURISTIC_AUDIT":
        raise ValueError("expected v0.4.28.44 context audit")
    if data.get("accepted") != 0 or data.get("train_ready") is not False:
        raise ValueError("audit approval state not safe")
    rows = data.get("audit_records")
    if not isinstance(rows, list) or len(rows) != data.get("audited_context"):
        raise ValueError("invalid audit records/count")
    ids = set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"] or row["id"] in ids:
            raise ValueError("invalid or duplicate IDs")
        if row.get("review_status") != "pending" or row.get("train_eligible") is not False:
            raise ValueError("unsafe candidate status")
        ids.add(row["id"])
    return rows

def sample(audit, size=50, seed=42845):
    rows = validate_audit(audit)
    if not isinstance(size, int) or size <= 0 or size > len(rows):
        raise ValueError("size must be between 1 and audited context count")
    # Hash ranking is deterministic and independent of input order or Python RNG.
    ordered = sorted(rows, key=lambda x: (hashlib.sha256((str(seed) + ":" + x["id"]).encode()).hexdigest(), x["id"]))
    selected = ordered[:size]
    return {
        "version": VERSION, "mode": "HUMAN_REVIEW_SAMPLE",
        "audit_sha256": digest(audit), "source_sha256": audit.get("source_sha256"),
        "population": len(rows), "sample_size": size, "seed": seed,
        "sampling_method": "deterministic_SHA256_rank_simple_random_like",
        "dimensions": list(DIMENSIONS), "records": [{
            "id": row["id"], "source_line": row["source_line"],
            "question": row["question"], "answer": row["answer"],
            "audit_status": row.get("audit_status"), "flags": row.get("flags", []),
            "ratings": {dimension: None for dimension in DIMENSIONS},
            "reviewer_notes": "", "review_status": "pending",
        } for row in selected],
        "accepted": 0, "train_ready": False, "runtime_modified": False
    }

def wilson(successes, trials, z=1.959963984540054):
    if trials == 0:
        return None
    p = successes / trials
    den = 1 + z*z / trials
    center = (p + z*z/(2*trials))/den
    margin = z * math.sqrt(p*(1-p)/trials + z*z/(4*trials*trials))/den
    return [max(0.0, center-margin), min(1.0, center+margin)]

def evaluate(template):
    if template.get("version") != VERSION or template.get("mode") != "HUMAN_REVIEW_SAMPLE":
        raise ValueError("expected v0.4.28.45 review sample")
    rows = template.get("records")
    if not isinstance(rows, list) or len(rows) != template.get("sample_size") or not rows:
        raise ValueError("invalid review records")
    ids = set()
    complete = positive = failed = unresolved = 0
    per_dimension = {k: {"pass": 0, "fail": 0, "unknown": 0, "pending": 0} for k in DIMENSIONS}
    for row in rows:
        rid = row.get("id")
        if not isinstance(rid, str) or not rid or rid in ids:
            raise ValueError("duplicate or invalid review ID")
        ids.add(rid)
        ratings = row.get("ratings")
        if not isinstance(ratings, dict) or set(ratings) != set(DIMENSIONS):
            raise ValueError("invalid rating fields")
        for k in DIMENSIONS:
            v = ratings[k]
            if v is not None and v not in VALID:
                raise ValueError("invalid rating: " + k)
            per_dimension[k][v if v is not None else "pending"] += 1
        values = list(ratings.values())
        if any(x is None for x in values):
            unresolved += 1
        elif any(x == "unknown" for x in values):
            unresolved += 1
        else:
            complete += 1
            if all(x == "pass" for x in values):
                positive += 1
            else:
                failed += 1
    # Strict all-dimensions pass; unknown and partial ratings never become positives.
    # Denominator for estimated precision only fully determined cases; report missingness.
    return {
        "version": VERSION, "mode": "HUMAN_REVIEW_PRECISION_REPORT",
        "population": template.get("population"), "sample_size": len(rows),
        "fully_adjudicated": complete, "all_dimensions_pass": positive,
        "any_dimension_fail": failed, "unresolved": unresolved,
        "dimension_counts": per_dimension,
        "observed_precision": positive/complete if complete else None,
        "wilson_95_ci": wilson(positive, complete),
        "precision_estimable_without_missingness_bias": unresolved == 0 and complete > 0,
        "accepted": 0, "train_ready": False, "evaluation_ready": False,
        "runtime_modified": False,
        "note": "Wilson CI is an approximate binomial interval, not finite-population adjusted. Nonresponse or ambiguous review can bias observed precision. Audit and rights checks remain required."
    }

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--audit")
    p.add_argument("--review")
    p.add_argument("--output", required=True)
    p.add_argument("--size", type=int, default=50)
    p.add_argument("--seed", type=int, default=42845)
    args = p.parse_args()
    if bool(args.audit) == bool(args.review):
        p.error("specify exactly one of --audit or --review")
    data = json.loads(Path(args.audit or args.review).read_text(encoding="utf-8"))
    result = sample(data, args.size, args.seed) if args.audit else evaluate(data)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {k: v for k, v in result.items() if k in ("version", "mode", "population", "sample_size", "fully_adjudicated", "all_dimensions_pass", "unresolved", "observed_precision", "wilson_95_ci", "train_ready")}
    print(json.dumps(summary, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
