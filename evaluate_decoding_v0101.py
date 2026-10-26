"""Evaluate frozen-model decoders; reference text is used only after generation."""
import argparse
import csv
import importlib
import json
from pathlib import Path
from semantic_decode_v0101 import decode

CONFIGS = [
    ("greedy", 1, 1., 1., 32),
    ("beam3", 3, 1., 1., 32),
    ("beam5", 5, 1., 1., 32),
    ("greedy_r105", 1, 1.05, 1., 32),
    ("greedy_r110", 1, 1.10, 1., 32),
    ("greedy_r120", 1, 1.20, 1., 32),
    ("beam3_r110", 3, 1.10, 1., 32),
    ("beam5_lp08", 5, 1., .8, 32),
    ("beam5_lp12", 5, 1., 1.2, 32),
    ("greedy_len16", 1, 1., 1., 16),
    ("greedy_len64", 1, 1., 1., 64),
]

def prefix_length(a, b):
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n

def evaluate(model, tokenizer, cases, configurations=CONFIGS):
    rows = []
    for case in cases:
        prompt = case["prompt"]
        reference = case["reference"]
        ref_ids = tokenizer.encode(reference, add_bos=False)
        for name, width, rep, length, cap in configurations:
            result = decode(model, tokenizer, prompt, beam_width=width,
                            repetition_penalty=rep, length_penalty=length, max_new_tokens=cap)
            rows.append(dict(id=case["id"], split=case.get("split", "dev"),
                             decoder=name, output=result.text, reference=reference,
                             exact_match=result.text.strip() == reference.strip(),
                             matched_prefix_tokens=prefix_length(result.token_ids, ref_ids),
                             generated_tokens=len(result.token_ids),
                             latency_ms=round(result.elapsed_ms, 2),
                             normalized_log_score=round(result.score, 5)))
    return rows

def main():
    ap = argparse.ArgumentParser(description="Frozen checkpoint decoder comparison")
    ap.add_argument("--cases", required=True)
    ap.add_argument("--factory", required=True, help="module:function returning (model, tokenizer)")
    ap.add_argument("--output", default="results/decoding_comparison_v0101.json")
    args = ap.parse_args()
    if ":" not in args.factory:
        ap.error("--factory must be module:function")
    module_name, function_name = args.factory.split(":", 1)
    model, tokenizer = getattr(importlib.import_module(module_name), function_name)()
    cases = json.loads(Path(args.cases).read_text(encoding="utf-8-sig"))
    if not isinstance(cases, list):
        raise ValueError("cases must be a JSON array")
    rows = evaluate(model, tokenizer, cases)
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    with dest.with_suffix(".csv").open("w", newline="", encoding="utf-8-sig") as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    summary = {}
    for name in sorted({row["decoder"] for row in rows}):
        subset = [r for r in rows if r["decoder"] == name]
        summary[name] = {"n": len(subset),
                         "exact_match": sum(r["exact_match"] for r in subset) / len(subset),
                         "mean_prefix": sum(r["matched_prefix_tokens"] for r in subset) / len(subset),
                         "mean_latency_ms": sum(r["latency_ms"] for r in subset) / len(subset)}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("wrote:", dest, dest.with_suffix(".csv"))

if __name__ == "__main__":
    main()
