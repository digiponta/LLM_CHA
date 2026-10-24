"""v0.8.0.24: read-only inventory of human-curated holdout records.

This tool does not create evidence, attest independence, or modify datasets.
"""
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

REQUIRED = ("id", "evaluation_kind", "question", "reference_answer",
            "source_url", "source_excerpt")
PLACEHOLDERS = ("replace-with", "ここに", "sample", "example", "テスト用の仮")


def inspect(path, minimum=5):
    source = Path(path)
    if not source.is_file():
        return {"status": "INPUT_NOT_FOUND", "path": str(source),
                "written": False}
    try:
        data = json.loads(source.read_text(encoding="utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        return {"status": "INVALID_JSON", "error": str(exc), "written": False}
    if not isinstance(data, dict) or not isinstance(data.get("records"), list):
        return {"status": "INVALID_FORMAT", "written": False}
    records = data["records"]
    issues = []
    seen = set()
    for index, row in enumerate(records):
        if not isinstance(row, dict):
            issues.append({"index": index, "issues": ["INVALID_ROW"]})
            continue
        errors = []
        for field in REQUIRED:
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append("MISSING_" + field.upper())
        identifier = row.get("id")
        if isinstance(identifier, str) and identifier.strip():
            if identifier in seen:
                errors.append("DUPLICATE_ID")
            seen.add(identifier)
        if row.get("evaluation_kind") != "UNSEEN_FACT":
            errors.append("NOT_UNSEEN_FACT")
        url = row.get("source_url")
        if isinstance(url, str) and url.strip():
            parsed = urlparse(url)
            if parsed.scheme not in ("https", "http") or not parsed.netloc:
                errors.append("INVALID_SOURCE_URL")
        if any(token in str(row.get(field, "")).casefold()
               for field in REQUIRED for token in PLACEHOLDERS):
            errors.append("PLACEHOLDER")
        if errors:
            issues.append({"index": index, "issues": errors})
    attested = data.get("independent_source_attested") is True
    status = ("READY_FOR_FORMAL_GATE"
              if len(records) >= minimum and not issues and attested
              else "NOT_READY")
    reasons = []
    if not records:
        reasons.append("EMPTY_HOLDOUT")
    elif len(records) < minimum:
        reasons.append("INSUFFICIENT_RECORDS")
    if not attested:
        reasons.append("SOURCE_INDEPENDENCE_NOT_ATTESTED")
    return {"status": status, "record_count": len(records),
            "minimum_required": minimum, "issues": issues, "reasons": reasons,
            "source_independence_attested": attested,
            "semantic_independence_verified": False,
            "written": False,
            "next_step": "python prepare_holdout_v08023.py " + str(source)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", default="data/curated_holdout.json")
    args = parser.parse_args()
    print(json.dumps(inspect(args.source), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
