#!/usr/bin/env python3
"""LLM_CHA v0.4.28.47: dialogue-boundary-aware QA candidate reconstruction.

Fail-closed: Only explicit conversation IDs/boundaries AND alternating roles qualify.
Plain unstructured lines are never paired. This is not a human approval step.
"""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

VERSION = "v0.4.28.47"
ROLE = re.compile(r"^\s*(ユーザー|User|Human|アシスタント|Assistant|Bot)\s*[:：]\s*(.*)$", re.I)
BOUNDARY = re.compile(r"^\s*(?:---+|===+|<\|dialogue_start\|>|\[dialogue\s+[^\]]+\])\s*$", re.I)
QUESTION = re.compile(r"(?:[？?]|ですか[。]?|ますか[。]?|でしょうか[。]?)$")
USER_ROLES = {"ユーザー", "user", "human"}
ASSISTANT_ROLES = {"アシスタント", "assistant", "bot"}

def role_of(label):
    s = label.lower()
    return "user" if s in USER_ROLES else "assistant" if s in ASSISTANT_ROLES else None

def parse_text(text):
    dialogues, current, boundaries, ambiguous = [], [], 0, 0
    def flush():
        nonlocal current
        if current:
            dialogues.append(current)
            current = []
    for lineno, original in enumerate(text.splitlines(), 1):
        if BOUNDARY.fullmatch(original):
            flush()
            boundaries += 1
            continue
        if not original.strip():
            # Blank lines can divide conversations but cannot identify a conversation on their own.
            flush()
            boundaries += 1
            continue
        match = ROLE.match(original)
        if not match:
            ambiguous += 1
            flush()
            continue
        role = role_of(match.group(1))
        utterance = match.group(2).strip()
        if not role or not utterance:
            ambiguous += 1
            flush()
            continue
        current.append({"role": role, "text": utterance, "source_line": lineno})
    flush()
    return dialogues, {"explicit_boundary_events": boundaries, "unparseable_lines": ambiguous}

def parse_json(data):
    # Only arrays of dialogues with an explicit id and turns array.
    dialogs = data.get("dialogues") if isinstance(data, dict) else None
    if not isinstance(dialogs, list):
        raise ValueError("JSON input needs dialogues array with id and turns")
    results = []
    ids = set()
    for dialogue in dialogs:
        if not isinstance(dialogue, dict) or not isinstance(dialogue.get("id"), str) or not dialogue["id"] or dialogue["id"] in ids:
            raise ValueError("each dialogue needs unique id")
        ids.add(dialogue["id"])
        turns = dialogue.get("turns")
        if not isinstance(turns, list):
            raise ValueError("dialogue turns must be a list")
        parsed = []
        for i, row in enumerate(turns):
            if not isinstance(row, dict) or not isinstance(row.get("role"), str) or not isinstance(row.get("text"), str):
                raise ValueError("turn needs role/text")
            role = role_of(row["role"])
            if role is None:
                raise ValueError("unrecognized role")
            parsed.append({"role": role, "text": row["text"].strip(), "source_line": i + 1})
        results.append((dialogue["id"], parsed))
    return results, {"explicit_boundary_events": len(results), "unparseable_lines": 0}

def reconstruct(dialogues, source_hash, metadata=None):
    outputs, counts, skipped = [], Counter(), Counter()
    for dialogue_id, turns in dialogues:
        for i, turn in enumerate(turns):
            if turn["role"] != "user" or not QUESTION.search(turn["text"]):
                continue
            counts["questions_seen"] += 1
            if i + 1 >= len(turns):
                skipped["no_next_turn"] += 1
                continue
            nxt = turns[i + 1]
            if nxt["role"] != "assistant":
                skipped["not_assistant_response"] += 1
                continue
            if not nxt["text"] or QUESTION.search(nxt["text"]):
                skipped["empty_or_question_answer"] += 1
                continue
            if len(turn["text"]) > 250 or len(nxt["text"]) > 500:
                skipped["length_limit"] += 1
                continue
            raw_id = dialogue_id + "\0" + str(i) + "\0" + turn["text"] + "\0" + nxt["text"]
            rid = "jfqa47-" + hashlib.sha256(raw_id.encode()).hexdigest()[:20]
            outputs.append({
                "id": rid, "dialogue_id": dialogue_id, "question_turn_index": i,
                "question": turn["text"], "answer": nxt["text"],
                "source_question_line": turn["source_line"], "source_answer_line": nxt["source_line"],
                "type": "context", "extraction_method": "explicit_boundary_and_roles",
                "review_status": "pending", "human_verified": False,
                "license_audited": False, "privacy_audited": False, "train_eligible": False})
            counts["candidate_pairs"] += 1
    return {"version": VERSION, "mode": "BOUNDARY_GROUNDED_QA_CANDIDATES",
            "source_sha256": source_hash, "source_diagnostics": metadata or {},
            "dialogue_count": len(dialogues), "questions_seen": counts["questions_seen"],
            "candidate_count": len(outputs), "skip_reasons": dict(skipped),
            "accepted": 0, "pending": len(outputs), "train_ready": False,
            "evaluation_ready": False, "runtime_modified": False,
            "notes": ["Only explicitly bounded dialogues are paired.",
                      "Role labels do not prove semantic relevance or factual correctness.",
                      "All outputs need independent QA review and rights/privacy audit."],
            "candidates": outputs}

def build_text(text):
    parsed, metadata = parse_text(text)
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    # Every pair needs explicit conversation boundaries. Unseparated dialogue runs may be concatenated,
    # so the source must include at least one identifiable boundary marker.
    if metadata["explicit_boundary_events"] == 0:
        return reconstruct([], sha, {**metadata, "boundary_evidence_missing": True})
    return reconstruct([(f"text-dialogue-{n+1}", turns) for n, turns in enumerate(parsed)], sha, metadata)

def build_json(data):
    parsed, metadata = parse_json(data)
    sha = hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return reconstruct(parsed, sha, metadata)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True)
    p.add_argument("--format", choices=("text", "json"), default="text")
    p.add_argument("--output", default="results/japanese_foundation_boundary_qa_v042847.json")
    args = p.parse_args()
    raw = Path(args.input).read_text(encoding="utf-8-sig")
    result = build_text(raw) if args.format == "text" else build_json(json.loads(raw))
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("version","dialogue_count","candidate_count","questions_seen","skip_reasons","accepted","train_ready","runtime_modified")}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
