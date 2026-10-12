"""v0.2.33.82.7: read-only proposition truth/provenance overlay.

Overlay is an optional JSONL of human-reviewed records, never automatically
created or updated by conversation. Missing entries inherit subject state.
An explicit proposition state may only RESTRICT, never override a subject block.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

BLOCKED = frozenset({"FALSE", "OUTDATED", "CONTESTED"})
VALID = frozenset({"TRUE", "FALSE", "UNVERIFIED", "CONTESTED", "OUTDATED"})

def proposition_id(subject: str, statement: str, provenance: str) -> str:
    blob = json.dumps([subject, statement, provenance], ensure_ascii=False, separators=(",", ":"))
    return sha256(blob.encode("utf-8")).hexdigest()[:24]

@dataclass(frozen=True)
class Decision:
    proposition_id: str
    state: str
    source: str
    allowed: bool

class TruthOverlay:
    def __init__(self, path: str | None = None):
        self.rows: dict[str, tuple[str, str]] = {}
        if not path:
            return
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(p)
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            key, state = row["proposition_id"], row["truth_state"]
            if not isinstance(key, str) or len(key) != 24 or any(c not in "0123456789abcdef" for c in key):
                raise ValueError("invalid proposition_id")
            if state not in VALID or key in self.rows:
                raise ValueError("invalid or duplicate truth state")
            self.rows[key] = (state, str(row.get("provenance", "")))

    def decide(self, subject: str, statement: str, provenance: str,
               subject_state: str, subject_allowed: bool) -> Decision:
        pid = proposition_id(subject, statement, provenance)
        row = self.rows.get(pid)
        # A subject-level denial cannot be bypassed by a TRUE proposition.
        state = row[0] if row else subject_state
        allowed = bool(subject_allowed) and state not in BLOCKED and state in VALID
        source = row[1] if row and row[1] else provenance
        return Decision(pid, state, source, allowed)
