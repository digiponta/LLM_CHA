#!/usr/bin/env python3
"""Export verified-structure RealPersonaChat dialogues for recover_dialogue_qa_v042848.py.

Accepts JSON {"dialogues":[{"id":...,"turns":[{"role":...,"text":...}]}]}
or JSONL with one such dialogue object per line.
No inferred speaker, role, conversation ID or dialogue boundary.
"""
import argparse
import json
from pathlib import Path

ROLES = {"user", "assistant", "human", "bot", "ユーザー", "アシスタント"}
NORMALIZED = {"human": "user", "bot": "assistant",
              "ユーザー": "user", "アシスタント": "assistant"}

def convert(data, split="train"):
    dialogs = data.get("dialogues") if isinstance(data, dict) else None
    if not isinstance(dialogs, list):
        raise ValueError("Source requires a dialogues array; inspect original format first")
    result, seen = [], set()
    for item in dialogs:
        if not isinstance(item, dict):
            raise ValueError("Dialogue must be an object")
        identifier = item.get("id")
        if not isinstance(identifier, str) or not identifier.strip() or identifier in seen:
            raise ValueError("Dialogue ID must be unique, nonempty string")
        seen.add(identifier)
        turns = item.get("turns")
        if not isinstance(turns, list) or not turns:
            raise ValueError("Dialogue must have nonempty turns")
        cleaned = []
        for turn in turns:
            if not isinstance(turn, dict) or not isinstance(turn.get("role"), str):
                raise ValueError("Turn requires a role")
            role = turn["role"].strip().lower()
            if role not in ROLES:
                raise ValueError("Unknown role; cannot infer speakers: " + role)
            message = turn.get("text")
            if not isinstance(message, str) or not message.strip():
                raise ValueError("Turn requires nonempty text")
            cleaned.append({"role": NORMALIZED.get(role, role), "text": message.strip()})
        result.append({"id": identifier, "turns": cleaned})
    return {"dialogues": result}

def load(path, fmt):
    text = Path(path).read_text(encoding="utf-8-sig")
    if fmt == "json":
        return json.loads(text)
    if fmt == "jsonl":
        return {"dialogues": [json.loads(line) for line in text.splitlines() if line.strip()]}
    raise ValueError("Unsupported input format")

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True, help="Existing dialogue-structured JSON or JSONL")
    ap.add_argument("--format", choices=("json", "jsonl"), default="json")
    ap.add_argument("--split", default="train", help="Provenance label only, not used to invent IDs")
    ap.add_argument("--output", default="data/realpersonachat_dialogues.json")
    args = ap.parse_args()
    output = convert(load(args.input, args.format), args.split)
    target = Path(args.output)
    if target.resolve() == Path(args.input).resolve():
        raise ValueError("Input and output paths must differ")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"dialogue_count":len(output["dialogues"]),
                      "turn_count":sum(len(d["turns"]) for d in output["dialogues"]),
                      "output":str(target), "inferred_ids":0,"inferred_roles":0},ensure_ascii=False,indent=2))

if __name__ == "__main__":
    main()
