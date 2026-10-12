"""v0.2.33.82.8: explicit human-reviewed proposition truth overlay CLI.

Separate admin workflow; never automatically judges propositions, never edits
the original corpus, topic context or main truth-store records.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile
from proposition_truth_v0233827 import TruthOverlay, VALID

ID_PATTERN = re.compile(r"^[0-9a-f]{24}$")

def apply_review(path: Path, pid: str, state: str, evidence: str,
                 reviewer: str, reason: str) -> None:
    if not ID_PATTERN.fullmatch(pid):
        raise ValueError("Expected a 24-digit hexadecimal proposition ID")
    if state not in VALID:
        raise ValueError("Invalid truth state")
    if not evidence.strip() or not reviewer.strip() or not reason.strip():
        raise ValueError("evidence, reviewer, and reason are required")
    if path.exists():
        existing = TruthOverlay(str(path))  # fail on corrupt/duplicate records
        rows = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                rows[row["proposition_id"]] = row
    else:
        rows = {}
    if pid in rows and rows[pid]["truth_state"] != state:
        raise ValueError("Conflicting review: explicitly investigate before changing state")
    rows[pid] = {
        "proposition_id": pid,
        "truth_state": state,
        "provenance": evidence.strip(),
        "reviewer": reviewer.strip(),
        "reason": reason.strip(),
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".truth-review-", dir=str(path.parent), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as out:
            for key in sorted(rows):
                out.write(json.dumps(rows[key], ensure_ascii=False) + "\n")
            out.flush()
            os.fsync(out.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)

def main() -> None:
    parser = argparse.ArgumentParser(description="Manual proposition truth review")
    parser.add_argument("--file", required=True)
    parser.add_argument("--id", required=True)
    parser.add_argument("--state", required=True, choices=sorted(VALID))
    parser.add_argument("--evidence", required=True, help="Independently reviewed source reference")
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--reason", required=True)
    args = parser.parse_args()
    apply_review(Path(args.file), args.id, args.state,
                 args.evidence, args.reviewer, args.reason)
    print(f"review=STORED proposition_id={args.id} truth_state={args.state}")
    print("Restart chat.py after setting LLM_CHA_PROPOSITION_TRUTH to this file.")

if __name__ == "__main__":
    main()
