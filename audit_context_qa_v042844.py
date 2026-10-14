#!/usr/bin/env python3
"""v0.4.28.44: offline context QA audit; never auto-approve candidates."""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

VERSION = "v0.4.28.44"
USER = re.compile(r"^(?:ユーザー|User|Human)\s*[:：]\s*", re.I)
ASSISTANT = re.compile(r"^(?:アシスタント|Assistant|Bot)\s*[:：]\s*", re.I)
QUESTION = re.compile(r"(?:[?？]|ですか[。]?|ますか[。]?|でしょうか[。]?)$")
TOPIC_SHIFT = re.compile(r"^(?:ところで|話は変わりますが|別の話ですが|さて[、,])")
SHORT = re.compile(r"^(?:はい|いいえ|そうです|違います|わかりません|不明です)[。.!！]?$")


def make_rows(text):
    rows = {}
    for n, raw in enumerate(text.splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        raw = raw.strip()
        role = "user" if USER.match(raw) else ("assistant" if ASSISTANT.match(raw) else "unmarked")
        normalized = USER.sub("", raw) if role == "user" else ASSISTANT.sub("", raw) if role == "assistant" else raw
        rows[n] = {"text": normalized.strip(), "role": role}
    return rows


def audit(source_text, coverage, sample_limit=100):
    if sample_limit < 0:
        raise ValueError("sample_limit must be nonnegative")
    sha = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    if coverage.get("version") != "v0.4.28.43" or coverage.get("mode") != "UNVERIFIED_QA_COVERAGE_DIAGNOSTICS":
        raise ValueError("input must be a v0.4.28.43 diagnostic export")
    if coverage.get("source_sha256") != sha:
        raise ValueError("source hash mismatch: use the exact source used by v0.4.28.43")
    if coverage.get("accepted") != 0 or coverage.get("train_ready") is not False:
        raise ValueError("input approval flags inconsistent")
    rows = make_rows(source_text)
    candidates = coverage.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("candidates must be a list")
    result = []
    non_context = 0
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError("invalid candidate")
        if candidate.get("review_status") != "pending" or candidate.get("train_eligible") is not False:
            raise ValueError("input candidate unexpectedly approved/eligible")
        if candidate.get("type") != "context":
            non_context += 1
            continue
        num = candidate.get("source_line")
        if not isinstance(num, int) or isinstance(num, bool):
            raise ValueError("invalid source line")
        first = rows.get(num)
        second = rows.get(num + 1)
        reasons = []
        if first is None or first["text"] != candidate.get("question"):
            reasons.append("question_source_mismatch")
        if second is None or second["text"] != candidate.get("answer"):
            reasons.append("answer_source_mismatch_or_nonadjacent")
        if first and second:
            if first["role"] == "assistant" or second["role"] == "user":
                reasons.append("unexpected_speaker_order")
            if first["role"] != "unmarked" and second["role"] == "unmarked":
                reasons.append("unmarked_answer_after_speaker_question")
            if TOPIC_SHIFT.match(second["text"]):
                reasons.append("possible_topic_shift")
            if QUESTION.search(second["text"]):
                reasons.append("answer_is_question")
            if len(second["text"]) < 4 and not SHORT.fullmatch(second["text"]):
                reasons.append("very_short_answer")
        status = "review_priority_high" if reasons else "review_priority_normal"
        result.append({
            "id": candidate.get("id"), "question": candidate.get("question"),
            "answer": candidate.get("answer"), "source_line": num,
            "source_question_role": first["role"] if first else None,
            "source_answer_role": second["role"] if second else None,
            "audit_status": status, "flags": reasons,
            "review_status": "pending", "human_verified": False,
            "train_eligible": False
        })
    summary = Counter(x["audit_status"] for x in result)
    flags = Counter(f for x in result for f in x["flags"])
    return {
        "version": VERSION, "mode": "CONTEXT_QA_HEURISTIC_AUDIT",
        "source_sha256": sha, "audited_context": len(result),
        "non_context_untouched": non_context, "audit_status_counts": dict(summary),
        "flag_counts": dict(flags), "sample_limit": sample_limit,
        "review_samples": [*sorted(result, key=lambda x: (x["audit_status"] != "review_priority_high", x["source_line"]))][:sample_limit],
        "audit_records": result, "accepted": 0, "train_ready": False,
        "evaluation_ready": False, "runtime_modified": False,
        "note": "Heuristic triage only. No verified precision, semantic matching, license check, privacy check or automatic approval."
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", default="data/japanese_foundation_v0218.txt")
    p.add_argument("--coverage", default="results/japanese_foundation_qa_coverage_v042843.json")
    p.add_argument("--output", default="results/japanese_foundation_context_audit_v042844.json")
    p.add_argument("--sample-limit", type=int, default=100)
    a = p.parse_args()
    text = Path(a.input).read_text(encoding="utf-8-sig")
    data = json.loads(Path(a.coverage).read_text(encoding="utf-8"))
    out = audit(text, data, a.sample_limit)
    path = Path(a.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("version", "audited_context", "non_context_untouched",
        "audit_status_counts", "flag_counts", "accepted", "train_ready", "runtime_modified")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
