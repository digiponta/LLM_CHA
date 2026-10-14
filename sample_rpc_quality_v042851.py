#!/usr/bin/env python3
"""LLM_CHA v0.4.28.51: reproducible, bounded-memory Native RPC review sample.

Hash-priority sampling over existing v0.4.28.50 JSONL candidates.
Sample is AI/human REVIEW INPUT, never verified or train-ready.
"""
import argparse
import hashlib
import heapq
import json
from pathlib import Path

VERSION = "v0.4.28.51"
DIMENSIONS = ("relevance", "semantic_consistency", "context_independence",
              "factual_correctness", "training_suitability")

def create_sample(input_path, size=50, seed=42851):
    if not isinstance(size, int) or size < 1:
        raise ValueError("size must be >= 1")
    selected = []
    seen = set()
    examined = 0
    sha = hashlib.sha256()
    with Path(input_path).open("rb") as stream:
        for line_no, raw in enumerate(stream, 1):
            sha.update(raw)
            if not raw.strip():
                continue
            item = json.loads(raw)
            if not isinstance(item, dict):
                raise ValueError(f"invalid candidate on line {line_no}")
            rid = item.get("id")
            if not isinstance(rid, str) or not rid or rid in seen:
                raise ValueError(f"missing or duplicate id on line {line_no}")
            seen.add(rid)
            if (item.get("source_kind") != "native_rpc_pair"
                or item.get("source_split") not in ("train", "val", "test")
                or item.get("review_status") != "pending"
                or item.get("train_eligible") is not False
                or item.get("human_verified") is not False
                or not isinstance(item.get("question"), str)
                or not item["question"].strip()
                or not isinstance(item.get("answer"), str)
                or not item["answer"].strip()):
                raise ValueError(f"unsafe/invalid candidate on line {line_no}")
            examined += 1
            priority = int.from_bytes(hashlib.sha256(f"{seed}:{rid}".encode()).digest(), "big")
            # Keep the k smallest hash values. Distinct ID is a deterministic tie-breaker.
            score = -priority
            sample_record = (score, rid, item)
            if len(selected) < size:
                heapq.heappush(selected, sample_record)
            elif score > selected[0][0] or (score == selected[0][0] and rid > selected[0][1]):
                heapq.heapreplace(selected, sample_record)
    if examined < size:
        raise ValueError(f"not enough eligible candidates: {examined} < {size}")
    rows = [t[2] for t in sorted(selected, key=lambda t: (-t[0], t[1]))]
    return {
        "version": VERSION, "mode": "NATIVE_RPC_QA_REVIEW_SAMPLE",
        "source_file_sha256": sha.hexdigest(), "population": examined,
        "sample_size": size, "seed": seed,
        "sampling_method": "sha256_hash_priority_without_replacement",
        "dimensions": list(DIMENSIONS),
        "records": [{
            "id": r["id"], "source_split": r["source_split"],
            "source_line": r.get("source_line"),
            "question": r["question"], "answer": r["answer"],
            "ratings": {k: None for k in DIMENSIONS},
            "reviewer_notes": "", "review_status": "pending",
            "human_verified": False, "train_eligible": False
        } for r in rows],
        "accepted": 0, "train_ready": False,
        "evaluation_ready": False, "runtime_modified": False,
        "note": "Sample is for independent QA review only. Do not interpret source pairs as factually correct or approved."
    }

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True)
    p.add_argument("--output", default="results/rpc_review_sample_v042851.json")
    p.add_argument("--size", type=int, default=50)
    p.add_argument("--seed", type=int, default=42851)
    args = p.parse_args()
    result = create_sample(args.input, args.size, args.seed)
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.resolve() == Path(args.input).resolve():
        raise ValueError("output must differ from input")
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in
          ("version", "population", "sample_size", "seed", "accepted", "train_ready", "runtime_modified")},
          ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
