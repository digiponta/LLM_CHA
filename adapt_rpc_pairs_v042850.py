#!/usr/bin/env python3
"""LLM_CHA v0.4.28.50: native RPC user/assistant pair adapter.

Each JSONL row is an independent pair, NOT a recovered dialogue.
No ID/role/turn reconstruction, automatic approval or runtime changes.
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

VERSION = "v0.4.28.50"

def process(path, output, split="train", max_records=None):
    if split not in ("train", "val", "test"):
        raise ValueError("split must be train, val or test")
    if max_records is not None and max_records < 1:
        raise ValueError("max_records must be positive")
    source = Path(path)
    target = Path(output)
    if source.resolve() == target.resolve():
        raise ValueError("input and output must differ")
    target.parent.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    sample = []
    digest = hashlib.sha256()
    # Write JSONL streaming: 112MB input need not fit in RAM.
    with source.open("rb") as fin, target.open("w", encoding="utf-8") as fout:
        for line_number, raw in enumerate(fin, 1):
            if max_records is not None and counts["rows_examined"] >= max_records:
                break
            digest.update(raw)
            if not raw.strip():
                continue
            counts["rows_examined"] += 1
            try:
                record = json.loads(raw.decode("utf-8-sig"))
            except (ValueError, UnicodeError):
                counts["invalid_json"] += 1
                continue
            if not isinstance(record, dict) or set(record) != {"user", "assistant"}:
                counts["invalid_schema"] += 1
                continue
            question, answer = record["user"], record["assistant"]
            if not isinstance(question, str) or not isinstance(answer, str) or not question.strip() or not answer.strip():
                counts["empty_or_invalid_text"] += 1
                continue
            rid = f"rpc-{split}-{line_number:09d}"
            candidate = {
                "id": rid, "source_split": split, "source_line": line_number,
                "source_kind": "native_rpc_pair", "dialogue_id": None,
                "dialogue_boundary_verified": False,
                "question": question.strip(), "answer": answer.strip(),
                "review_status": "pending", "human_verified": False,
                "license_audited": False, "privacy_audited": False,
                "train_eligible": False
            }
            fout.write(json.dumps(candidate, ensure_ascii=False) + "\n")
            counts["candidate_pairs"] += 1
            if len(sample) < 3:
                sample.append({"id": rid, "source_line": line_number})
    report = {
        "version": VERSION, "mode": "NATIVE_RPC_PAIR_CANDIDATES",
        "source": str(source), "source_split": split,
        "source_sha256_examined_prefix": digest.hexdigest(),
        "max_records": max_records, "counts": dict(counts),
        "sample_metadata": sample, "output": str(target),
        "accepted": 0, "train_ready": False, "evaluation_ready": False,
        "runtime_modified": False,
        "note": "Row IDs are provenance keys, not dialogue IDs. Native pair provenance does not guarantee semantic correctness, conversational boundaries, licensing, privacy or train suitability."
    }
    manifest = target.with_suffix(target.suffix + ".manifest.json")
    manifest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True)
    ap.add_argument("--split", choices=("train", "val", "test"), required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--max-records", type=int)
    args = ap.parse_args()
    r = process(args.input, args.output, args.split, args.max_records)
    print(json.dumps({k: r[k] for k in ("version", "source_split", "counts", "accepted", "train_ready", "runtime_modified", "output")}, ensure_ascii=False, indent=2))
if __name__ == "__main__":
    main()
