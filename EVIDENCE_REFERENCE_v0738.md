# LLM_CHA v0.7.38 — Source Evidence Reference Counting

Expands the reference-count policy from v0.7.37 to unverified
`RAW_CONCEPT_EVIDENCE` and `CORPUS_MEMORY` responses.

- Creates a PENDING Candidate keyed by the **exact local evidence answer**,
  source provenance, route, and concept.
- The Wikipedia extract is excluded from the Candidate identity and counter.
- The same unchanged evidence returned in a separate turn increments the count.
- Default threshold is 10; approval occurs on reference **11**.
- Modified content produces a new identity and begins at 1.
- Distinct routes or sources are deliberately tracked separately.
- Previously approved matching source evidence is not counted again.
- No counting for Wikipedia-only, identity, greeting, or unrelated generation.
- User-approved or source-validated factual truth is not implied by usage approval.

**Operational limitation:** New PENDING source evidence changes the Candidate
snapshot. An existing Experimental Adapter checkpoint may no longer match
the pending set until a new `/sleep` is run. Additionally, v0.7.38 adds
source-level Approved entries to the dual-memory Approved JSONL, not to
the existing Trusted internalized knowledge model weights.

## PowerShell

```powershell
git fetch origin
git switch --track origin/v0.7.38
python -m unittest -v test_evidence_reference_v0738.py test_reference_approval_v0737.py
$env:LLM_CHA_MEMORY_FIRST="1"
$env:LLM_CHA_MEMORY_FIRST_MODE="constrained"
$env:LLM_CHA_AUTO_APPROVE_REFERENCES="10"
python chat_window_v061.py
```

Test by submitting the **same unverified source query** 11 times in
separate turns (e.g. `真空管`), and inspect the diagnostic
`[evidence_reference: status=..., count=..., promoted=...]`.
After the 11th reference, inspect `data/approved_v071.jsonl`.

Keep one writer process while counting: v0.7.38 does not include
cross-process transactional locks.
