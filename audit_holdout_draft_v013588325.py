"""Pre-review diagnostic: lexical overlap and multi-turn completeness.

This is NOT a semantic independence proof or a human review substitute.
"""
import argparse
import json
import re
import unicodedata
from pathlib import Path

def normalize(s):
    return re.sub(r"\\s+", "", unicodedata.normalize("NFKC", s).casefold())

def corpus_strings(path):
    p = Path(path)
    if p.suffix.lower() == ".json":
        obj = json.loads(p.read_text(encoding="utf-8-sig"))
        strings = []
        def visit(x):
            if isinstance(x, str):
                strings.append(x)
            elif isinstance(x, dict):
                for k, v in x.items():
                    if k in {"question", "query", "prompt", "text", "content", "utterance", "input"}:
                        visit(v)
                    elif isinstance(v, (dict, list)):
                        visit(v)
            elif isinstance(x, list):
                for v in x: visit(v)
        visit(obj)
        return strings
    return p.read_text(encoding="utf-8-sig").splitlines()

def audit(dataset, sources=None):
    sources = sources or []
    if dataset.get("schema") != "llm-cha-independent-holdout-v1":
        raise ValueError("INVALID_SCHEMA")
    cases = dataset.get("cases", [])
    source_data = {}
    for path in sources:
        source_data[str(path)] = set(normalize(x) for x in corpus_strings(path) if isinstance(x, str) and x.strip())
    flags = []
    for c in cases:
        turns = c.get("turns") or []
        user_turns = [t["text"] for t in turns if t.get("role") == "user" and isinstance(t.get("text"), str)]
        if c.get("category") == "multi_turn" and len(user_turns) < 2:
            flags.append({"id": c.get("id"), "type": "SINGLE_TURN_IN_MULTI_TURN_CATEGORY"})
        for text in user_turns:
            n = normalize(text)
            for path, entries in source_data.items():
                if n and n in entries:
                    flags.append({"id": c.get("id"), "type": "EXACT_NORMALIZED_OVERLAP", "source": path})
        if c.get("review_state") != "APPROVED":
            flags.append({"id": c.get("id"), "type": "HUMAN_REVIEW_PENDING"})
    counts = {}
    for flag in flags: counts[flag["type"]] = counts.get(flag["type"], 0) + 1
    return {"status": "REVIEW_REQUIRED", "independence_verified": False,
            "scope": "DEVELOPMENT_DIAGNOSTIC_ONLY",
            "case_count": len(cases), "sources_compared": list(source_data),
            "flag_counts": counts, "flags": flags,
            "limitations": ["No semantic paraphrase search", "No training exposure proof",
                            "No human review", "No runtime evaluation"]}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", default="data/independent_holdout_draft_v013588325.json")
    p.add_argument("--compare", nargs="*", default=[])
    p.add_argument("--output", default="results/holdout_draft_audit_v013588325.json")
    a = p.parse_args()
    report = audit(json.loads(Path(a.dataset).read_text(encoding="utf-8-sig")), a.compare)
    out = Path(a.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "flag_counts": report["flag_counts"],
                      "sources_compared": report["sources_compared"],
                      "report": str(out)}, ensure_ascii=False))
if __name__ == "__main__": main()
