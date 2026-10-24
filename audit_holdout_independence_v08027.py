"""v0.8.0.27: read-only provenance and semantic-review triage.

This is NOT a semantic entailment model. Human review is mandatory.
No external URLs are fetched, no evidence is fabricated, and no attestations
or holdout files are modified.
"""
import argparse
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse
from unapproved_llm_intake_v074446 import _read
from detect_holdout_leakage_v08025 import compare

FIELDS = ("id", "question", "reference_answer", "source_url", "source_excerpt")
STOP = {"について", "とは", "ですか", "という", "あります", "何ですか", "どの", "それぞれ",
        "である", "した", "ありますか", "教えて", "ください"}

def terms(value):
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    # Word-sized latin/digit sequences and Japanese sequences; this is a weak
    # topic heuristic, not a general-purpose tokenizer.
    raw = re.findall(r"[a-z0-9]+|[一-龯々ァ-ヶー]{2,}|[ぁ-ん]{3,}", text)
    return set(t for t in raw if t not in STOP)

def source_issues(row):
    issues = []
    for field in FIELDS:
        if not isinstance(row.get(field), str) or not row[field].strip():
            issues.append("MISSING_" + field.upper())
    url = row.get("source_url")
    if isinstance(url, str):
        parsed = urlparse(url.strip())
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
            issues.append("SOURCE_URL_REQUIRES_HTTPS_HOST")
    if row.get("evaluation_kind") != "UNSEEN_FACT":
        issues.append("NOT_UNSEEN_FACT")
    return issues

def review(source, store, manual_review=None, lexical_threshold=0.80):
    if not 0 < lexical_threshold <= 1:
        raise ValueError("lexical_threshold must be in (0,1]")
    source, store = Path(source), Path(store)
    if not source.is_file():
        return {"status": "INPUT_NOT_FOUND", "written": False}
    if not store.is_file():
        return {"status": "TRAINING_STORE_NOT_FOUND", "written": False}
    try:
        dataset = json.loads(source.read_text(encoding="utf-8-sig"))
        training = _read(store)["candidates"]
        if not isinstance(dataset, dict) or not isinstance(dataset.get("records"), list):
            return {"status": "INVALID_FORMAT", "written": False}
        checks = {}
        if manual_review:
            path = Path(manual_review)
            if path.is_file():
                data = json.loads(path.read_text(encoding="utf-8-sig"))
                if not isinstance(data, dict) or not isinstance(data.get("reviews"), list):
                    return {"status": "INVALID_REVIEW_FORMAT", "written": False}
                checks = {r["id"]: r for r in data["reviews"]
                          if isinstance(r, dict) and isinstance(r.get("id"), str)}
    except (ValueError, OSError, UnicodeError, TypeError, KeyError) as exc:
        return {"status": "INVALID_INPUT", "error": str(exc), "written": False}

    findings = []
    seen = set()
    for idx, row in enumerate(dataset["records"]):
        if not isinstance(row, dict):
            findings.append({"index": idx, "flags": ["INVALID_ROW"]})
            continue
        rid = row.get("id")
        flags = source_issues(row)
        if not isinstance(rid, str) or rid in seen:
            flags.append("DUPLICATE_OR_INVALID_ID")
        if isinstance(rid, str):
            seen.add(rid)
        # Surface topic overlap even without lexical match. Does not certify
        # semantic non-overlap when no match is detected.
        h_terms = terms(row.get("question")) | terms(row.get("reference_answer"))
        matches = []
        for t in training:
            if not isinstance(t, dict):
                continue
            ref_text = " ".join(str(t.get(k, "")) for k in ("subject", "natural_language", "canonical_text"))
            common = sorted(h_terms & terms(ref_text))
            score = max(compare(row.get(k), t.get(f)) for k in ("question", "reference_answer")
                        for f in ("subject", "natural_language", "canonical_text"))
            if common or score >= lexical_threshold:
                matches.append({"candidate_id": t.get("id"), "common_terms": common,
                                "max_lexical_similarity": score})
        if matches:
            flags.append("POSSIBLE_SEMANTIC_OR_LEXICAL_OVERLAP")
        att = checks.get(rid, {}) if isinstance(rid, str) else {}
        # Require explicit per-record human assessments. The script neither
        # checks remote URLs nor treats user attestation as scientific proof.
        fields = ("source_checked", "answer_checked", "training_nonoverlap_checked")
        manually_checked = all(att.get(f) is True for f in fields)
        if not manually_checked:
            flags.append("HUMAN_REVIEW_PENDING")
        if len(matches) and not (att.get("overlap_manually_resolved") is True):
            flags.append("OVERLAP_REVIEW_PENDING")
        findings.append({"index": idx, "id": rid, "flags": flags,
                         "overlap_candidates": matches, "human_checks_complete": manually_checked})
    status = "NOT_READY" if not findings else (
        "REVIEW_REQUIRED" if any(f["flags"] for f in findings)
        else "MANUAL_REVIEW_RECORDED")
    return {"status": status, "record_count": len(findings), "findings": findings,
            "source_urls_fetched": False, "semantic_independence_verified": False,
            "training_exposure_excluded": False, "formal_holdout_approved": False,
            "written": False}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", default="data/holdout_review_candidates_v08026.json")
    parser.add_argument("--store", default="data/unapproved_llm_candidates_v074446.json")
    parser.add_argument("--review", default=None, help="optional human review JSON")
    args = parser.parse_args()
    print(json.dumps(review(args.source, args.store, args.review),
                     ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
