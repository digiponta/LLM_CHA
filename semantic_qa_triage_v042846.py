#!/usr/bin/env python3
"""v0.4.28.46 rule-based semantic consistency triage (not semantic verification)."""
import argparse
import json
import re
from collections import Counter
from pathlib import Path
from review_precision_v042845 import DIMENSIONS

VERSION = "v0.4.28.46"
NEG = re.compile(r"(?:ではない|ではありません|できない|できません|しない|しません|違います|いいえ)")
UNCERTAIN = re.compile(r"(?:不明|わからない|分かりません|確認できない|かもしれない|可能性がある)")
TOPIC = re.compile(r"^(?:ところで|話は変わ|別の話|さて[、,])")
PRONOUN = re.compile(r"(?:それ|あれ|これ|その|あの|彼|彼女|前述|さっき|先ほど)")
COPULA = re.compile(r"(?:です|だ|である)(?:[。.!！]|$)")
YESNO = re.compile(r"(?:ですか|ますか|でしょうか|できますか|[？?])$")
STOP = set("はがをにのとでもからよりしてですますかこれそれあれということため")
def terms(value):
    return set(x for x in re.findall(r"[一-龥]{2,}|[ァ-ヴー]{2,}|[A-Za-z]{3,}", value) if x not in STOP)

def inspect(question, answer):
    flags = []
    if not question or not answer:
        flags.append("empty_text")
    if TOPIC.search(answer):
        flags.append("possible_topic_shift")
    if PRONOUN.search(answer):
        flags.append("context_dependent_expression")
    if UNCERTAIN.search(answer):
        flags.append("uncertain_answer")
    if YESNO.search(answer):
        flags.append("answer_looks_like_question")
    if NEG.search(answer) and not NEG.search(question):
        flags.append("negative_answer_review")
    qa, aa = terms(question), terms(answer)
    if len(qa) >= 2 and len(aa) >= 2 and not qa.intersection(aa):
        flags.append("low_lexical_overlap")
    return sorted(set(flags))

def analyze(sample):
    if sample.get("version") != "v0.4.28.45" or sample.get("mode") != "HUMAN_REVIEW_SAMPLE":
        raise ValueError("expected v0.4.28.45 HUMAN_REVIEW_SAMPLE")
    records = sample.get("records")
    if not isinstance(records, list) or len(records) != sample.get("sample_size") or not records:
        raise ValueError("sample mismatch")
    if sample.get("accepted") != 0 or sample.get("train_ready") is not False:
        raise ValueError("unsafe sample approval state")
    seen = set()
    result = []
    for row in records:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"] or row["id"] in seen:
            raise ValueError("duplicate or invalid sample id")
        seen.add(row["id"])
        if row.get("review_status") != "pending":
            raise ValueError("review status must remain pending")
        ratings = row.get("ratings")
        if not isinstance(ratings, dict) or set(ratings) != set(DIMENSIONS):
            raise ValueError("invalid ratings")
        if any(v not in (None, "pass", "fail", "unknown") for v in ratings.values()):
            raise ValueError("invalid rating value")
        question, answer = row.get("question"), row.get("answer")
        if not isinstance(question, str) or not isinstance(answer, str):
            raise ValueError("question and answer must be strings")
        flags = inspect(question, answer)
        result.append({"id": row["id"], "source_line": row.get("source_line"),
                       "flags": flags, "triage": "review_priority_high" if flags else "review_priority_normal",
                       "review_status": "pending", "train_eligible": False})
    return {"version": VERSION, "mode": "SEMANTIC_QA_HEURISTIC_TRIAGE",
            "sample_size": len(result), "flag_counts": dict(Counter(f for r in result for f in r["flags"])),
            "priority_counts": dict(Counter(r["triage"] for r in result)),
            "records": result, "accepted": 0, "train_ready": False,
            "evaluation_ready": False, "runtime_modified": False,
            "note": "Flags indicate possible issues, not semantic contradictions or factual errors; no approval or precision estimate."}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--review", required=True)
    p.add_argument("--output", default="results/japanese_foundation_semantic_triage_v042846.json")
    args = p.parse_args()
    report = analyze(json.loads(Path(args.review).read_text(encoding="utf-8")))
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("version", "sample_size", "priority_counts", "flag_counts",
                                           "accepted", "train_ready", "runtime_modified")}, ensure_ascii=False, indent=2))
if __name__ == "__main__":
    main()
