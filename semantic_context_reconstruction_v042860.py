#!/usr/bin/env python3
"""LLM_CHA v0.4.28.60: conservative semantic-context retrieval and reconstruction.

Lexical baseline over a bounded set of subjects, predicates and objects.
Never silently resolve conflicting user claims or treat candidates as truths.
No model inference, training or chat runtime mutation.
"""
import argparse
import json
from pathlib import Path
from incremental_semantic_memory_v042859 import load

VERSION = "v0.4.28.60"
ALIASES = {
    "car": ("車", "自動車", "マイカー", "car"),
    "movie": ("映画", "movie"),
    "owns": ("持って", "所有", "買った", "保有"),
    "likes": ("好き", "好み"),
}

def matches_query(query, item):
    obj = item["object"]
    words = ALIASES.get(obj, (obj,))
    # Require an explicit object/topic hit; avoid a fact triggered merely by '私'.
    return any(word in query for word in words)

def retrieve(memory, query, top_k=5):
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be nonempty")
    if top_k < 1:
        raise ValueError("top_k must be positive")
    candidates = [dict(p) for p in memory.get("proposition_index", [])
                  if matches_query(query, p)]
    conflicts = {(p["subject"], p["predicate"], p["object"])
                 for p in memory.get("conflict_candidates", [])}
    for p in candidates:
        key = p["subject"], p["predicate"], p["object"]
        p["conflict_unresolved"] = key in conflicts
        p["latest_source_turn"] = max(p["source_turns"])
    # Most recent evidence first; deterministic secondary sort.
    candidates.sort(key=lambda p: (-p["latest_source_turn"], p["predicate"],
                                    p["object"], str(p["polarity"])))
    # Never truncate an unresolved conflict group to a single polarity.
    chosen = candidates[:top_k]
    selected_keys = {(p["subject"], p["predicate"], p["object"])
                     for p in chosen if p["conflict_unresolved"]}
    for p in candidates[top_k:]:
        if (p["subject"], p["predicate"], p["object"]) in selected_keys:
            chosen.append(p)
    return chosen

def reconstruct(memory, query, top_k=5, recent_turns=3, max_chars=1200):
    if recent_turns < 0 or max_chars < 1:
        raise ValueError("invalid context limits")
    found = retrieve(memory, query, top_k)
    recent = memory.get("recent_turns", [])[-recent_turns:] if recent_turns else []
    lines = ["【未検証の会話記憶：断定しない】"]
    for p in found:
        polarity = "肯定" if p["polarity"] else "否定"
        conflict = "・矛盾/状態変化未解決" if p["conflict_unresolved"] else ""
        lines.append(f'{p["subject"]} {p["predicate"]} {p["object"]}: {polarity}'
                     f' (根拠ターン:{",".join(map(str,p["source_turns"]))}{conflict})')
    lines.append("【直近の会話】")
    for t in recent:
        lines.append(f'{t["role"]}: {t["text"]}')
    lines.append("【現在の質問】")
    lines.append(query)
    # Fail closed rather than silently cutting evidence or the question.
    context = "\n".join(lines)
    if len(context) > max_chars:
        return {"status": "budget_exceeded", "context": None,
                "characters_needed": len(context), "max_chars": max_chars,
                "retrieved": found, "recent_turn_count": len(recent),
                "train_ready": False}
    return {"status": "ready", "context": context, "characters_needed": len(context),
            "max_chars": max_chars, "retrieved": found,
            "recent_turn_count": len(recent), "train_ready": False}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--memory", required=True)
    ap.add_argument("--query", required=True)
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--recent-turns", type=int, default=3)
    ap.add_argument("--max-chars", type=int, default=1200)
    ap.add_argument("--output", default="results/semantic_context_v042860.json")
    a=ap.parse_args()
    result=reconstruct(load(a.memory),a.query,a.top_k,a.recent_turns,a.max_chars)
    result.update({"version":VERSION,"query":a.query,"runtime_modified":False})
    output=Path(a.output)
    if output.resolve()==Path(a.memory).resolve():raise ValueError("output cannot overwrite memory")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in
         ("version","status","characters_needed","recent_turn_count","train_ready")},
         ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
