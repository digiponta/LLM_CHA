#!/usr/bin/env python3
"""LLM_CHA v0.4.28.49: inspect native RPC JSONL structure without guessing conversation IDs.
Only prints field names, types, structural counts, and anonymized diagnostics.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

VERSION = "v0.4.28.49"
CANDIDATE_IDS = ("id", "dialogue_id", "conversation_id", "dialog_id")

def inspect_file(path, max_records=1000):
    if max_records < 1:
        raise ValueError("max_records must be >= 1")
    keys, types, id_presence, duplicate_ids = Counter(), Counter(), Counter(), 0
    ids = set()
    records = malformed = no_id = 0
    structural_examples = []
    with Path(path).open(encoding="utf-8-sig") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            if records >= max_records:
                break
            records += 1
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                malformed += 1
                continue
            if not isinstance(obj, dict):
                types[type(obj).__name__] += 1
                continue
            keys.update(obj.keys())
            present = [k for k in CANDIDATE_IDS if k in obj]
            if not present:
                no_id += 1
            else:
                k = present[0]
                v = obj[k]
                id_presence[k + ":" + type(v).__name__] += 1
                if isinstance(v, (str, int)) and not isinstance(v, bool):
                    identifier = (k, str(v))
                    if identifier in ids:
                        duplicate_ids += 1
                    ids.add(identifier)
            if len(structural_examples) < 3:
                # Never display raw user texts, IDs, or conversation content.
                structural_examples.append({
                    "line": line_no, "fields": sorted(obj.keys()),
                    "field_types": {k: type(v).__name__ for k, v in obj.items()},
                    "array_lengths": {k: len(v) for k, v in obj.items() if isinstance(v, list)},
                    "nested_object_fields": {k: sorted(v.keys()) for k, v in obj.items() if isinstance(v, dict)}
                })
    return {"version": VERSION, "mode": "STRUCTURAL_JSONL_DIAGNOSTIC",
            "records_examined": records, "malformed": malformed,
            "no_identified_id": no_id, "duplicate_id_values_in_sample": duplicate_ids,
            "field_counts": dict(keys), "id_field_types": dict(id_presence),
            "nonobject_types": dict(types), "structural_examples": structural_examples,
            "train_ready": False, "runtime_modified": False,
            "note": "IDs repeated across turn rows may represent a valid dialogue; do not deduplicate without turn ordering."}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True)
    ap.add_argument("--limit", type=int, default=1000)
    ap.add_argument("--output", default="results/rpc_schema_diagnostic_v042849.json")
    a = ap.parse_args()
    report = inspect_file(a.input, a.limit)
    output = Path(a.output)
    if output.resolve() == Path(a.input).resolve():
        raise ValueError("Input and output paths must differ")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
if __name__ == "__main__":
    main()
