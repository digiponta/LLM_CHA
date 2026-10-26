"""Per-question paired decoder audit v0.10.1.3.

Requires the full decoding_sweep_v01012.json, not the summary CSV.
Never treats training-associated cases as independent holdout.
"""
import argparse
import csv
import json
from pathlib import Path

def paired_audit(payload, length=48, baseline="greedy", challenger="beam3"):
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("Full sweep JSON with non-empty 'records' is required; summary CSV is insufficient.")
    def index(method):
        subset = [r for r in records if r.get("method") == method and r.get("max_new_tokens") == length]
        indexed = {}
        for row in subset:
            key = str(row["id"])
            if key in indexed:
                raise ValueError(f"Duplicate record {method}/{length}/{key}")
            indexed[key] = row
        return indexed
    a, b = index(baseline), index(challenger)
    if not a or a.keys() != b.keys():
        raise ValueError("Unpaired or missing test cases")
    rows = []
    for key in sorted(a):
        old, new = a[key], b[key]
        if old.get("reference") != new.get("reference"):
            raise ValueError(f"Reference mismatch for {key}")
        old_ok, new_ok = bool(old["exact_match"]), bool(new["exact_match"])
        category = ("both_correct" if old_ok and new_ok else
                    "improved" if not old_ok and new_ok else
                    "regressed" if old_ok and not new_ok else "both_incorrect")
        rows.append({
            "id": key, "category": category,
            "baseline_output": old["output"], "challenger_output": new["output"],
            "reference": old["reference"],
            "baseline_prefix": old["matched_prefix_tokens"],
            "challenger_prefix": new["matched_prefix_tokens"],
            "baseline_tokens": old["generated_tokens"],
            "challenger_tokens": new["generated_tokens"],
            "baseline_cap_hit": old["hit_token_cap"],
            "challenger_cap_hit": new["hit_token_cap"],
        })
    counts = {s: sum(x["category"] == s for x in rows) for s in
              ("both_correct","improved","regressed","both_incorrect")}
    counts["baseline_correct"] = counts["both_correct"] + counts["regressed"]
    counts["challenger_correct"] = counts["both_correct"] + counts["improved"]
    counts["net_gain"] = counts["improved"] - counts["regressed"]
    return {"protocol": "TRAIN_ASSOCIATED_DEV_NOT_HOLDOUT",
            "baseline": baseline, "challenger": challenger,
            "max_new_tokens": length, "count": len(rows),
            "summary": counts, "records": rows}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="results/decoding_sweep_v01012.json")
    p.add_argument("--output", default="results/decoding_pair_audit_v01013.json")
    p.add_argument("--length", type=int, default=48)
    args = p.parse_args()
    source = json.loads(Path(args.input).read_text(encoding="utf-8-sig"))
    report = paired_audit(source, length=args.length)
    path = Path(args.output); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    csv_path = path.with_suffix(".csv")
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(report["records"][0]))
        writer.writeheader(); writer.writerows(report["records"])
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print("report:", path, csv_path)

if __name__ == "__main__":
    main()
