#!/usr/bin/env python3
"""LLM_CHA v0.4.28.42: conservative offline Japanese QA coverage extraction.

Candidate-only. Nothing produced by this program is approved for training.
"""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

VERSION = "v0.4.28.42"
KINDS = ("definition", "comparison", "causal", "conditional", "negation", "context")
RULES = (
    ("definition", re.compile(r"^(.{1,45}?)とは[、,]?(.{2,180})[。．.]?$"), "とは何ですか"),
    ("comparison", re.compile(r"^(.{1,30}?)と(.{1,30}?)の違いは[、,]?(.{2,180})[。．.]?$"), "の違いは何ですか"),
    ("causal", re.compile(r"^(.{1,45}?)の理由は[、,]?(.{2,180})[。．.]?$"), "の理由は何ですか"),
    ("conditional", re.compile(r"^(.{1,60}?)場合[、,](.{2,180})[。．.]?$"), "場合、どうなりますか"),
    ("negation", re.compile(r"^(.{1,60}?)ではない[。．.]?$"), "ですか"),
)
QUESTION_MARK = re.compile(r"[?？]$")
SPEAKER = re.compile(r"^(?:ユーザー|User|Human|Assistant|アシスタント|Bot)\s*[:：]\s*(.*)$", re.I)


def clean(line):
    line = line.strip()
    m = SPEAKER.match(line)
    return (m.group(1) if m else line).strip()


def extract(text, max_candidates=10000):
    if max_candidates < 1:
        raise ValueError("max_candidates must be positive")
    lines = [clean(x) for x in text.splitlines()]
    lines = [x for x in lines if x and not x.startswith("#")]
    seen = set()
    result = []
    def add(kind, question, answer, line_index):
        question, answer = question.strip(), answer.strip()
        if not question or not answer or question == answer:
            return
        if len(question) > 150 or len(answer) > 250:
            return
        key = (question, answer)
        if key in seen or len(result) >= max_candidates:
            return
        seen.add(key)
        identifier = hashlib.sha256((kind + "\0" + question + "\0" + answer).encode("utf-8")).hexdigest()[:20]
        result.append({
            "id": "jfqa42-" + identifier, "type": kind,
            "question": question, "answer": answer,
            "source_line": line_index + 1,
            "review_status": "pending", "human_verified": False,
            "license_audited": False, "privacy_audited": False,
            "train_eligible": False
        })

    for idx, line in enumerate(lines):
        for kind, rule, ending in RULES:
            m = rule.fullmatch(line)
            if not m:
                continue
            if kind == "definition":
                add(kind, m.group(1) + ending, m.group(2).rstrip("。．."), idx)
            elif kind == "comparison":
                add(kind, m.group(1) + "と" + m.group(2) + ending, m.group(3).rstrip("。．."), idx)
            elif kind == "causal":
                add(kind, m.group(1) + ending, m.group(2).rstrip("。．."), idx)
            elif kind == "conditional":
                add(kind, m.group(1) + ending, m.group(2).rstrip("。．."), idx)
            elif kind == "negation":
                add(kind, m.group(1) + ending, line.rstrip("。．."), idx)
            break
        # Adjacent explicit Q/A pair only; do not infer unstated context.
        if idx + 1 < len(lines) and QUESTION_MARK.search(line) and not QUESTION_MARK.search(lines[idx + 1]):
            answer = lines[idx + 1]
            if len(answer) >= 2:
                add("context", line, answer, idx)
    return result


def build(text, source_path, limit=10000):
    candidates = extract(text, limit)
    counts = Counter(c["type"] for c in candidates)
    return {
        "version": VERSION, "mode": "UNVERIFIED_QA_COVERAGE_CANDIDATES",
        "source": str(source_path), "source_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "candidate_count": len(candidates), "type_counts": {k: counts[k] for k in KINDS},
        "accepted": 0, "pending": len(candidates),
        "train_ready": False, "evaluation_ready": False, "runtime_modified": False,
        "notes": ["Heuristic extraction; answers may be false or out of context.",
                  "Line numbers refer to nonempty, non-comment normalized lines.",
                  "Source licensing and privacy must be independently audited.",
                  "Do not import candidates into v0.4.28.41 verified dataset without human review."],
        "candidates": candidates
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/japanese_foundation_v0218.txt")
    parser.add_argument("--output", default="results/japanese_foundation_qa_coverage_v042842.json")
    parser.add_argument("--max-candidates", type=int, default=10000)
    args = parser.parse_args()
    source = Path(args.input)
    result = build(source.read_text(encoding="utf-8-sig"), source, args.max_candidates)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in
        ("version", "candidate_count", "type_counts", "accepted", "pending", "train_ready", "runtime_modified")},
        ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
