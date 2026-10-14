#!/usr/bin/env python3
"""LLM_CHA v0.4.28.43: candidate-only Japanese QA pattern expansion and diagnostics."""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from expand_japanese_foundation_qa_v042842 import extract as extract_42, clean

VERSION = "v0.4.28.43"
KINDS = ("definition", "comparison", "causal", "conditional", "negation", "context")
SPEAKER_LINE = re.compile(r"^(ユーザー|User|Human|Assistant|アシスタント|Bot)\s*[:：]", re.I)
QUESTION = re.compile(r"(?:[?？]|ですか[。]?|ますか[。]?|でしょうか[。]?)$")
PATTERNS = (
    ("comparison", re.compile(r"^(.{1,40}?)と(.{1,40}?)は(?:どう|どのように)違(?:う|いますか)[。？?]?$")),
    ("causal", re.compile(r"^(?:なぜ|どうして)(.{2,100}?)(?:のですか|ですか|なの|[？?])$")),
    ("conditional", re.compile(r"^(?:もし)(.{2,110}?)なら[、,]?(.{2,160})[。]?$")),
    ("negation", re.compile(r"^(.{2,100}?)(?:できません|できない|しない|ではありません)[。]?$")),
)
def source_lines(text):
    return [(i + 1, clean(row), bool(SPEAKER_LINE.match(row.strip()))) for i, row in enumerate(text.splitlines()) if row.strip() and not row.lstrip().startswith("#")]

def propose(text, max_candidates=10000):
    if max_candidates < 1:
        raise ValueError("max_candidates must be positive")
    rows = source_lines(text)
    found, seen = [], set()
    def emit(kind, q, answer, position, rule):
        q, answer = q.strip(), answer.strip()
        if not q or not answer or q == answer or len(q) > 150 or len(answer) > 250:
            return False
        key = (q, answer)
        if key in seen or len(found) >= max_candidates:
            return False
        seen.add(key)
        identifier = hashlib.sha256((kind + "\x00" + q + "\x00" + answer).encode()).hexdigest()[:20]
        found.append({
            "id": "jfqa43-" + identifier, "type": kind, "question": q,
            "answer": answer, "source_line": position, "rule": rule,
            "review_status": "pending", "human_verified": False,
            "license_audited": False, "privacy_audited": False, "train_eligible": False
        })
        return True

    # Retain v42 candidates as a baseline, mapped to actual source lines if possible.
    old = extract_42(text, max_candidates)
    old_lines = source_lines(text)
    for item in old:
        index = item["source_line"] - 1
        physical = old_lines[index][0] if index < len(old_lines) else item["source_line"]
        emit(item["type"], item["question"], item["answer"], physical, "v042842")
    hit_lines = {c["source_line"] for c in found}
    for n, (position, line, speaker) in enumerate(rows):
        if len(found) >= max_candidates:
            break
        for kind, pattern in PATTERNS:
            match = pattern.fullmatch(line)
            if not match:
                continue
            if kind == "comparison":
                # A question without a documented answer is not an extractable QA pair.
                continue
            if kind == "causal":
                continue
            if kind == "conditional":
                emit(kind, "もし" + match.group(1) + "なら、どうなりますか", match.group(2).rstrip("。"), position, "conditional-if")
            else:
                emit(kind, match.group(1) + "できますか", line.rstrip("。"), position, "negation-predicate")
        # Q/A pairing only with explicit speaker roles or explicit question followed by unmarked answer.
        if QUESTION.search(line) and n + 1 < len(rows):
            next_pos, answer, next_speaker = rows[n+1]
            if (not QUESTION.search(answer) and len(answer) >= 2 and next_pos == position + 1 and
                (not speaker or next_speaker) and not answer.startswith(("Q:", "質問:"))):
                emit("context", line, answer, position, "adjacent-explicit-question")
    hit_lines |= {c["source_line"] for c in found}
    categorized = Counter()
    samples = []
    for position, line, speaker in rows:
        if position in hit_lines:
            continue
        label = ("question_without_answer" if QUESTION.search(line) else
                 "possible_comparison" if re.search(r"違い|比較|異な", line) else
                 "possible_causal" if re.search(r"なぜ|どうして|理由|原因", line) else
                 "possible_conditional" if re.search(r"もし|場合|なら|とき", line) else
                 "possible_negation" if re.search(r"ない|ません|否定", line) else "other")
        categorized[label] += 1
        if len(samples) < 50:
            samples.append({"source_line": position, "category": label, "preview": line[:120]})
    return found, {"source_nonempty_lines": len(rows), "unmatched_lines": sum(categorized.values()),
                   "unmatched_categories": dict(sorted(categorized.items())),
                   "unmatched_examples": samples}

def build(text, source, limit=10000):
    candidates, diagnostics = propose(text, limit)
    counter = Counter(c["type"] for c in candidates)
    baseline = extract_42(text, limit)
    return {
        "version": VERSION, "mode": "UNVERIFIED_QA_COVERAGE_DIAGNOSTICS",
        "source": str(source), "source_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "baseline_v042842_count": len(baseline), "candidate_count": len(candidates),
        "type_counts": {kind: counter[kind] for kind in KINDS},
        "accepted": 0, "pending": len(candidates),
        "train_ready": False, "evaluation_ready": False, "runtime_modified": False,
        "notes": ["Rule-based candidates are unverified and may be wrong.",
                  "Do not train on these candidates without independent human and rights/privacy review.",
                  "Context pairs must be manually checked for speaker and topic boundaries."],
        "diagnostics": diagnostics, "candidates": candidates
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/japanese_foundation_v0218.txt")
    parser.add_argument("--output", default="results/japanese_foundation_qa_coverage_v042843.json")
    parser.add_argument("--max-candidates", type=int, default=10000)
    args = parser.parse_args()
    text = Path(args.input).read_text(encoding="utf-8-sig")
    result = build(text, args.input, args.max_candidates)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in
        ("version", "baseline_v042842_count", "candidate_count", "type_counts", "accepted", "pending", "train_ready", "runtime_modified")},
        ensure_ascii=False, indent=2))
    print("unmatched_categories:", json.dumps(result["diagnostics"]["unmatched_categories"], ensure_ascii=False))
if __name__ == "__main__":
    main()
