"""v0.7.44.17 — corpus-to-cursor identity preflight.

CorpusMemoryRecord in v10.12.16 lacks a proposition ID. This adapter
does not fabricate a stable ID from text or list position.
"""
from dataclasses import dataclass
from evidence_cursor_v074416 import Evidence

@dataclass(frozen=True)
class BridgeReport:
    status: str
    count: int
    missing_ids: int
    missing_sources: int
    evidence: tuple[Evidence, ...]

def bridge_records(records, subject, truth_state="UNVERIFIED"):
    selected = [r for r in records if r.subject == subject]
    out = []
    missing_ids = 0
    missing_sources = 0
    for r in selected:
        proposition_id = getattr(r, "proposition_id", None)
        source = getattr(r, "source", None)
        if not proposition_id:
            missing_ids += 1
        if not source:
            missing_sources += 1
        if not proposition_id or not source:
            continue
        if truth_state != "UNVERIFIED":
            continue
        out.append(Evidence(proposition_id=str(proposition_id),
                            subject=r.subject, text=r.statement,
                            provenance=str(source), truth_state=truth_state))
    status = ("MISSING_ID" if missing_ids else
              "MISSING_SOURCE" if missing_sources else
              "READY" if out else "NO_ELIGIBLE_EVIDENCE")
    return BridgeReport(status,len(selected),missing_ids,missing_sources,tuple(out))
