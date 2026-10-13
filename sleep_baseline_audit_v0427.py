"""Read-only comparison for pre/post sleep captures, v0.4.27."""
import argparse
import json
from pathlib import Path
from persona_quality_annotation_v0423 import load_jsonl

def compare(before, after):
    def index(rows):
        out = {}
        for row in rows:
            question = row["question"].strip()
            if question in out:
                raise ValueError("duplicate question")
            out[question] = row
        return out
    a, b = index(before), index(after)
    if not a or set(a) != set(b):
        raise ValueError("before and after question sets must match")
    rows = []
    for q in sorted(a):
        x, y = a[q], b[q]
        rows.append({
            "question": q,
            "before_answer": x["answer"],
            "after_answer": y["answer"],
            "answer_changed": x["answer"] != y["answer"],
            "before_agreement": x["agreement"],
            "after_agreement": y["agreement"],
            "before_semantic_agreement": x["semantic_agreement"],
            "after_semantic_agreement": y["semantic_agreement"],
            "human_review_required": True,
        })
    return {
        "version": "v0.4.27",
        "matched_questions": len(rows),
        "changed_answers": sum(x["answer_changed"] for x in rows),
        "rows": rows,
        "quality_improvement_claimed": False,
        "checkpoint_comparability_verified": False,
        "sleep_causality_claimed": False,
        "independent_holdout_claimed": False,
        "training_enabled": False,
        "runtime_decisions_modified": False,
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--before", required=True)
    p.add_argument("--after", required=True)
    p.add_argument("--report", required=True)
    a = p.parse_args()
    try:
        result = compare(load_jsonl(a.before), load_jsonl(a.after))
        path = Path(a.report)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({k: v for k, v in result.items() if k != "rows"}, ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, TypeError) as e:
        p.exit(1, "sleep audit failed: " + str(e) + "\n")

if __name__ == "__main__":
    main()
