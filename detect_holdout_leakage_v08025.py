"""v0.8.0.25: read-only lexical leakage triage for curated holdouts.

Character n-gram and sequence similarity are weak semantic proxies. A clean
result is NEVER a semantic independence certificate or proof of non-exposure.
"""
import argparse
import json
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from unapproved_llm_intake_v074446 import _read


def normalize(value):
    if not isinstance(value, str):
        return ""
    return re.sub(r"\\s+", "", unicodedata.normalize("NFKC", value).casefold())


def grams(value, n=2):
    text = normalize(value)
    return {text[i:i+n] for i in range(max(0, len(text)-n+1))}


def compare(a, b):
    a, b = normalize(a), normalize(b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    ga, gb = grams(a), grams(b)
    dice = 2 * len(ga & gb) / (len(ga) + len(gb)) if ga and gb else 0.0
    seq = SequenceMatcher(None, a, b, autojunk=False).ratio()
    containment = min(len(a), len(b)) / max(len(a), len(b)) if a in b or b in a else 0.0
    return round(max(seq, dice, containment), 4)


def inspect(holdout, store, threshold=0.8):
    if not 0.0 < threshold <= 1.0:
        raise ValueError("threshold must be within (0, 1]")
    source = Path(holdout)
    if not source.is_file():
        return {"status": "INPUT_NOT_FOUND", "written": False}
    try:
        data = json.loads(source.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict) or not isinstance(data.get("records"), list):
            return {"status": "INVALID_FORMAT", "written": False}
        # A missing training store cannot establish non-overlap.
        training_path = Path(store)
        if not training_path.is_file():
            return {"status": "TRAINING_STORE_NOT_FOUND", "written": False}
        rows = _read(training_path)["candidates"]
    except (OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
        return {"status": "INVALID_INPUT", "error": str(exc), "written": False}
    details = []
    flagged = 0
    for i, record in enumerate(data["records"]):
        if not isinstance(record, dict):
            details.append({"index": i, "flags": ["INVALID_ROW"]})
            flagged += 1
            continue
        best = {"score": 0.0, "candidate_id": None, "field_pair": None}
        for candidate in rows:
            if not isinstance(candidate, dict):
                continue
            # Check across fields to catch answer/question leakage.
            for field in ("question", "reference_answer"):
                for target in ("natural_language", "canonical_text", "subject"):
                    score = compare(record.get(field), candidate.get(target))
                    if score > best["score"]:
                        best = {"score": score, "candidate_id": candidate.get("id"),
                                "field_pair": field + "/" + target}
        flags = []
        if best["score"] >= threshold:
            flags.append("POSSIBLE_LEXICAL_LEAKAGE")
        if not normalize(record.get("question")) or not normalize(record.get("reference_answer")):
            flags.append("INCOMPLETE_RECORD")
        if flags:
            flagged += 1
        details.append({"index": i, "id": record.get("id"), **best, "flags": flags})
    if not data["records"]:
        status = "NOT_READY"
        reasons = ["EMPTY_HOLDOUT"]
    elif flagged:
        status = "REVIEW_REQUIRED"
        reasons = ["POSSIBLE_OVERLAP_OR_INVALID_RECORD"]
    else:
        status = "NO_LEXICAL_FLAGS"
        reasons = []
    return {"status": status, "record_count": len(details),
            "training_candidate_count": len(rows), "flagged_count": flagged,
            "threshold": threshold, "reasons": reasons, "details": details,
            "semantic_independence_verified": False,
            "training_exposure_excluded": False, "written": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", default="data/curated_holdout.json")
    parser.add_argument("--store", default="data/unapproved_llm_candidates_v074446.json")
    parser.add_argument("--threshold", type=float, default=0.8)
    args = parser.parse_args()
    print(json.dumps(inspect(args.source, args.store, args.threshold),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
