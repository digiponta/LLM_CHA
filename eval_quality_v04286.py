"""v0.4.28.6 read-only triage of captured benchmark results.

No model invocation, learning, Truth Gate changes, or automated correctness claims.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

ABSTENTIONS = {"未学習です", "(no response)", ""}

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def gate_resolution(gate):
    if not isinstance(gate, str):
        return "NOT_RECORDED"
    match = re.search(r"\bresolution=([A-Z_]+)", gate)
    if match:
        return match.group(1)
    match = re.search(r"\bgate=([A-Z_]+)", gate)
    return match.group(1) if match else "NOT_RECORDED"

def triage(capture):
    if not isinstance(capture, dict) or not isinstance(capture.get("groups"), list):
        raise ValueError("invalid capture JSON")
    records = []
    categories = Counter()
    resolutions = Counter()
    statuses = Counter()
    ids = set()
    for group in capture["groups"]:
        if not isinstance(group, dict) or not isinstance(group.get("turns"), list):
            raise ValueError("invalid group")
        ident = group.get("id")
        if not isinstance(ident, str) or ident in ids or not re.fullmatch(r"[A-G]\d{1,2}", ident):
            raise ValueError("invalid/duplicate group id")
        ids.add(ident)
        status = group.get("status", "UNKNOWN")
        statuses[status] += 1
        for index, turn in enumerate(group["turns"], 1):
            if not isinstance(turn, dict) or not isinstance(turn.get("question"), str):
                raise ValueError("invalid turn")
            answer = turn.get("response")
            if answer is not None and not isinstance(answer, str):
                raise ValueError("invalid answer")
            resolved = gate_resolution(turn.get("gate"))
            resolutions[resolved] += 1
            categories[ident[0]] += 1
            abstain = answer is not None and answer.strip() in ABSTENTIONS
            bad_char = answer is not None and "\ufffd" in answer
            flags = []
            if answer is None: flags.append("MISSING_CAPTURE")
            if abstain: flags.append("ABSTENTION")
            if bad_char: flags.append("REPLACEMENT_IN_ANSWER")
            if resolved in {"ACCEPT", "KNOWN"} and bad_char:
                flags.append("REVIEW_ACCEPTED_MALFORMED")
            if answer is not None and not abstain:
                flags.append("HUMAN_REVIEW_REQUIRED")
            records.append({
                "id": ident, "turn": index, "category": ident[0],
                "mode": group.get("mode"), "question": turn["question"],
                "answer": answer, "gate_resolution": resolved,
                "process_status": status, "captured": answer is not None,
                "abstention": abstain, "flags": flags,
                "human_annotation": {
                    "relevance": None, "japanese_fluency": None,
                    "persona_consistency": None, "grounding": None,
                    "gate_appropriateness": None, "notes": ""
                }
            })
    return {
        "version": "v0.4.28.6", "assessment": "AUTOMATED_TRIAGE_ONLY",
        "human_quality_evaluated": False, "independent_holdout": False,
        "total_cases": len(capture["groups"]), "total_turns": len(records),
        "captured_answers": sum(r["captured"] for r in records),
        "abstentions": sum(r["abstention"] for r in records),
        "replacement_in_answers": sum("REPLACEMENT_IN_ANSWER" in r["flags"] for r in records),
        "category_counts": dict(sorted(categories.items())),
        "gate_resolution_counts": dict(sorted(resolutions.items())),
        "process_status_counts": dict(sorted(statuses.items())),
        "records": records
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    try:
        inp, out = Path(args.input), Path(args.output)
        if not inp.is_file() or inp.is_symlink():
            raise ValueError("input missing/symlink")
        if out.exists() or out.is_symlink():
            raise ValueError("output exists: overwrite prohibited")
        report = triage(json.loads(inp.read_text(encoding="utf-8")))
        report["capture_sha256"] = sha256(inp)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        print(json.dumps({k: report[k] for k in (
            "total_cases", "total_turns", "captured_answers",
            "abstentions", "replacement_in_answers",
            "gate_resolution_counts")}, ensure_ascii=False))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        ap.exit(1, f"quality triage failed: {exc}\n")

if __name__ == "__main__":
    main()
