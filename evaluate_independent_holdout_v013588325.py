"""Independent paired holdout scorer for v0.13.58.83.25.

Consumes manually reviewed labels and captured baseline/RSE runtime traces.
Does NOT infer answers, mint human approvals, or change chat.py.
"""
import argparse
import hashlib
import json
from pathlib import Path

CATEGORIES = {"paraphrase", "negation", "ambiguity", "multi_turn", "knowledge_collision"}
LABELS = {"ADOPT", "ABSTAIN", "PASS_THROUGH"}
DECISIONS = {"ADOPT", "ABSTAIN", "PASS_THROUGH"}

def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def validate(dataset, recordings):
    if dataset.get("schema") != "llm-cha-independent-holdout-v1":
        raise ValueError("INVALID_DATASET_SCHEMA")
    cases = dataset.get("cases")
    if not isinstance(cases, list) or len(cases) < 50:
        raise ValueError("MINIMUM_50_CASES_REQUIRED")
    ids = [c.get("id") for c in cases]
    if len(set(ids)) != len(ids) or any(not isinstance(i, str) or not i for i in ids):
        raise ValueError("INVALID_CASE_IDS")
    for c in cases:
        if c.get("category") not in CATEGORIES or not isinstance(c.get("turns"), list) or not c["turns"]:
            raise ValueError("INVALID_CASE: " + c["id"])
        for t in c["turns"]:
            if t.get("role") not in {"user", "assistant"} or not isinstance(t.get("text"), str) or not t["text"].strip():
                raise ValueError("INVALID_TURN: " + c["id"])
        if c.get("expected_decision") not in LABELS:
            raise ValueError("MISSING_HUMAN_LABEL: " + c["id"])
        if not c.get("reviewer") or not c.get("reviewed_at") or c.get("review_state") != "APPROVED":
            raise ValueError("HUMAN_REVIEW_REQUIRED: " + c["id"])
    if set(c["category"] for c in cases) != CATEGORIES:
        raise ValueError("MISSING_CATEGORY")
    independence = dataset.get("independence", {})
    if independence.get("human_attested") is not True or not independence.get("reviewer"):
        raise ValueError("INDEPENDENCE_ATTESTATION_REQUIRED")
    if independence.get("training_overlap") is not False or independence.get("development_overlap") is not False:
        raise ValueError("INDEPENDENCE_NOT_VERIFIED")
    if recordings.get("schema") != "llm-cha-paired-runtime-recordings-v1":
        raise ValueError("INVALID_RECORDINGS_SCHEMA")
    if recordings.get("dataset_digest") != digest(cases):
        raise ValueError("DATASET_DIGEST_MISMATCH")
    if recordings.get("same_checkpoint") is not True or recordings.get("same_knowledge_state") is not True:
        raise ValueError("UNPAIRED_RUNTIME_CONFIGURATION")
    if recordings.get("executed_chat_py") is not True:
        raise ValueError("REAL_RUNTIME_REQUIRED")
    rows = recordings.get("cases", [])
    if len(rows) != len(cases) or set(x.get("id") for x in rows) != set(ids):
        raise ValueError("MISSING_OR_DUPLICATE_RECORDINGS")
    for r in rows:
        for mode in ("off", "on"):
            run = r.get(mode, {})
            if run.get("decision") not in DECISIONS or not isinstance(run.get("answer"), str):
                raise ValueError("INVALID_RUNTIME_RECORD: " + str(r.get("id")))
            if not run.get("route") or not run.get("run_id"):
                raise ValueError("RUNTIME_PROVENANCE_REQUIRED: " + str(r.get("id")))
    return cases, {r["id"]: r for r in rows}

def rate(cases, records, mode):
    positive = [c for c in cases if c["expected_decision"] == "ADOPT"]
    negative = [c for c in cases if c["expected_decision"] != "ADOPT"]
    tp = sum(records[c["id"]][mode]["decision"] == "ADOPT" for c in positive)
    fp = sum(records[c["id"]][mode]["decision"] == "ADOPT" for c in negative)
    correct = sum(records[c["id"]][mode]["decision"] == c["expected_decision"] for c in cases)
    preserved = [c for c in cases if c.get("protected_knowledge") is True]
    preserved_ok = sum(records[c["id"]][mode].get("knowledge_correct") is True for c in preserved)
    unknown = [c for c in cases if c.get("unknown_expected") is True]
    unknown_ok = sum(records[c["id"]][mode]["decision"] == "ABSTAIN" for c in unknown)
    return {
        "count": len(cases), "tp": tp, "fp": fp, "positive_count": len(positive),
        "negative_count": len(negative), "precision": tp / (tp + fp) if tp + fp else None,
        "positive_coverage": tp / len(positive) if positive else None,
        "false_adoption_rate": fp / len(negative) if negative else None,
        "decision_accuracy": correct / len(cases),
        "protected_knowledge_count": len(preserved),
        "knowledge_retention": preserved_ok / len(preserved) if preserved else None,
        "unknown_count": len(unknown),
        "unknown_abstention_accuracy": unknown_ok / len(unknown) if unknown else None,
    }

def evaluate(dataset, recordings):
    cases, records = validate(dataset, recordings)
    off, on = rate(cases, records, "off"), rate(cases, records, "on")
    thresholds = {
        "precision": .90, "positive_coverage": .80, "false_adoption_rate": .05,
        "knowledge_retention": .98, "unknown_abstention_accuracy": .90,
    }
    checks = {k: (on[k] is not None and (on[k] <= v if k == "false_adoption_rate" else on[k] >= v))
              for k, v in thresholds.items()}
    return {
        "status": "PASS" if all(checks.values()) and on["knowledge_retention"] >= off["knowledge_retention"] else "FAIL",
        "scope": "HUMAN_REVIEWED_INDEPENDENT_PAIRED_RUNTIME",
        "dataset_digest": digest(cases), "checks": checks, "thresholds": thresholds,
        "baseline": off, "rse_enabled": on,
        "per_category": {k: {"baseline": rate([c for c in cases if c["category"] == k], records, "off"),
                             "rse_enabled": rate([c for c in cases if c["category"] == k], records, "on")}
                         for k in sorted(CATEGORIES)},
        "case_results": [{"id": c["id"], "category": c["category"], "expected": c["expected_decision"],
                          "off": records[c["id"]]["off"]["decision"], "on": records[c["id"]]["on"]["decision"]}
                         for c in cases],
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--recordings", required=True)
    parser.add_argument("--output", default="results/independent_holdout_v013588325.json")
    args = parser.parse_args()
    dataset, recordings = load_json(args.dataset), load_json(args.recordings)
    try:
        result = evaluate(dataset, recordings)
    except (ValueError, TypeError, KeyError, ZeroDivisionError) as exc:
        result = {"status": "NOT_READY", "reason": str(exc), "scope": "INDEPENDENT_HOLDOUT"}
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)

if __name__ == "__main__":
    main()
