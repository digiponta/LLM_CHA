"""Import lines of data-nagato.txt as unapproved Experimental candidates.

Default is dry-run. --commit updates only the Candidate JSONL store.
Run from LLM_CHA repository root.
"""
import argparse
import hashlib
import json
from pathlib import Path

from dual_semantic_memory_v071 import DualMemory, fingerprint, write_store


def import_lines(source, approved, candidates, limit=None, commit=False):
    source, approved, candidates = map(Path, (source, approved, candidates))
    if source.resolve() in {approved.resolve(), candidates.resolve()}:
        raise ValueError("Source cannot overlap a memory store")
    if limit is not None and limit < 1:
        raise ValueError("--limit must be positive")
    raw_bytes = source.read_bytes()
    raw_text = raw_bytes.decode("utf-8-sig")
    digest = hashlib.sha256(raw_bytes).hexdigest()
    entries = [(number, text.strip()) for number, text in
               enumerate(raw_text.splitlines(), 1) if text.strip()]
    if limit is not None:
        entries = entries[:limit]
    memory = DualMemory(approved, candidates)
    old_candidates = memory.candidates()
    old_approved = memory.approved()
    known = {r["id"] for r in old_candidates + old_approved}
    additions = []
    for line_number, answer in entries:
        question = f"data-nagato.txtの第{line_number}行の記述を教えて"
        if len(answer) > 12000:
            raise ValueError(f"Line {line_number} too long")
        record_id = fingerprint(question, answer)
        if record_id in known:
            continue
        additions.append({
            "id": record_id, "question": question, "answer": answer,
            "source_id": f"data-nagato.txt:sha256={digest}:line={line_number}",
            "status": "PENDING",
        })
        known.add(record_id)
    if commit and additions:
        if memory.candidates() != old_candidates:
            raise RuntimeError("Candidates changed during import")
        write_store(candidates, old_candidates + additions)
    return {
        "status": "COMMITTED" if commit else "DRY_RUN",
        "source": str(source), "source_sha256": digest,
        "selected_lines": len(entries), "new_pending": len(additions),
        "already_present": len(entries) - len(additions),
        "approved_modified": False, "auto_promote": False,
        "candidate_store": str(candidates),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="data/data-nagato.txt")
    parser.add_argument("--approved", default="data/approved_v071.jsonl")
    parser.add_argument("--candidates", default="data/candidates_v071.jsonl")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--commit", action="store_true")
    args = parser.parse_args()
    print(json.dumps(import_lines(args.source, args.approved, args.candidates,
                                  args.limit, args.commit),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
