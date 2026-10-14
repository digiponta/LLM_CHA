#!/usr/bin/env python3
"""LLM_CHA v0.4.28.48: explicit-dialogue import, provenance and QA reconstruction.

Input contract (JSON or JSONL):
{"dialogues":[{"id":"...", "turns":[{"role":"user","text":"..."},{"role":"assistant","text":"..."}]}]}
JSONL: one dialogue object per line with the same id/turns fields.

Never guess dialogue IDs, roles, or boundaries from flattened corpus lines.
"""
import argparse
import hashlib
import json
from pathlib import Path
from reconstruct_dialogue_qa_v042847 import parse_json, reconstruct

VERSION = "v0.4.28.48"

def load_dialogues(path, input_format):
    text = Path(path).read_text(encoding="utf-8-sig")
    if input_format == "json":
        data = json.loads(text)
    elif input_format == "jsonl":
        data = {"dialogues": [json.loads(row) for row in text.splitlines() if row.strip()]}
    else:
        raise ValueError("format must be json or jsonl")
    if not isinstance(data, dict) or not isinstance(data.get("dialogues"), list):
        raise ValueError("require explicit dialogues with unique IDs and turns")
    return data, hashlib.sha256(text.encode("utf-8")).hexdigest()

def build(data, source_hash):
    parsed, metadata = parse_json(data)
    if not parsed:
        raise ValueError("zero explicitly identified dialogues")
    for dialogue_id, turns in parsed:
        if not turns:
            raise ValueError("empty dialogue: " + dialogue_id)
        if any(not turn["text"] for turn in turns):
            raise ValueError("empty turn: " + dialogue_id)
    report = reconstruct(parsed, source_hash, metadata)
    report["version"] = VERSION
    report["mode"] = "SOURCE_GROUNDED_DIALOGUE_QA"
    report["source_format"] = "explicit_dialogue_id_and_roles"
    report["conversion_performed"] = True
    report["source_identity_verified"] = False
    report["notes"].append("Source identity, rights, privacy and QA relevance require independent verification.")
    return report

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True)
    ap.add_argument("--format", choices=("json", "jsonl"), required=True)
    ap.add_argument("--output", default="results/japanese_foundation_dialogue_qa_v042848.json")
    args = ap.parse_args()
    data, source_hash = load_dialogues(args.input, args.format)
    report = build(data, source_hash)
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("version", "dialogue_count", "questions_seen",
        "candidate_count", "accepted", "pending", "train_ready", "runtime_modified")}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
