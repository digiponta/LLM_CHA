# v0.7.44.3 Persona Gap Response Quality Gate — isolated prototype

This version adds a standalone `response_quality_gate_v07443.py` and unit tests.
It is **not yet wired into chat.py**. No production behavior changes.

## Test

```powershell
git pull
python -m unittest -v test_response_quality_gate_v07443.py
```

Actions: `ACCEPT` (ordinary reply), `REVIEW` (persona_gap without detectable defects),
`RETRY` (empty, invalid or repeated text), `HOLD` (unverified generated evidence).
The calling runtime must eventually implement bounded retry and safe fallback.
Trusted and Approved retrieval routes bypass these stylistic heuristics; their
truth and provenance rules still apply separately.

Limits: a simple rule-based test does not establish fluent Japanese, semantic
consistency or correct persona. The isolated prototype does not infer truth
from smooth phrasing. Evaluate against real generated logs before integration.
