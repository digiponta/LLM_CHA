"""v0.2.34.2: real subject-keyed corpus adapter for guarded restore.

Read-only. Current subject Truth State and authorization MUST be supplied by
the caller's authoritative gate; the adapter never infers truth from corpus.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable
from context_restore_validation_v023341 import (
    CurrentProposition, CurrentSubject, RestoreReport, validate_restored_context,
)
from grounded_expansion_v0233826 import PropositionCursor
from longterm_context_v02340 import ContextCheckpoint
from proposition_truth_v0233827 import TruthOverlay
from retrieval_first_runtime_v1012161 import resolve_subject, truth_allows_direct_retrieval

# The runtime uses one composed-answer provenance for every split proposition.
SubjectGate = Callable[[str], tuple[str, bool]]

def current_subjects_for_snapshot(
    snapshot: str,
    corpus_path: str | Path,
    subject_gate: SubjectGate,
) -> dict[str, CurrentSubject]:
    checkpoint = ContextCheckpoint.restore(snapshot)
    path = Path(corpus_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    current: dict[str, CurrentSubject] = {}
    for subject in checkpoint.topics:
        result = resolve_subject(path, subject)
        state, permitted = subject_gate(subject)
        if not isinstance(state, str) or not state:
            raise ValueError("subject gate omitted truth state")
        # Denial from either the current gate or the baseline truth policy wins.
        allowed = bool(permitted) and truth_allows_direct_retrieval(state)
        # Provenance and proposition splitting deliberately match chat.py.
        propositions = (
            tuple(CurrentProposition(p, result.provenance)
                  for p in PropositionCursor.split(result.answer))
            if result.hit else ()
        )
        current[subject] = CurrentSubject(propositions, state, allowed)
    return current

def restore_from_corpus(
    snapshot: str,
    corpus_path: str | Path,
    subject_gate: SubjectGate,
    overlay: TruthOverlay,
) -> RestoreReport:
    current = current_subjects_for_snapshot(snapshot, corpus_path, subject_gate)
    return validate_restored_context(snapshot, current, overlay)
