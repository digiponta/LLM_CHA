# v0.7.14 — Multi-Candidate & Trusted Retention Audit

This revision provides a **read-only evaluation harness**, not a new trained
adapter. The v0.7.13 `chat.py` routing remains unchanged.

The harness:
- Evaluates **each PENDING Candidate** with a real Experimental Adapter
  (or a deterministic test double).
- Requires exact generated-answer equality for consistency and labels any
  accepted answer `EXPERIMENTAL_UNVERIFIED`.
- Never asks Experimental for approved QA, retaining the approved answer.
- Rejects questions absent from Approved and Candidate stores without
  invoking Experimental.
- Produces structured results, including candidate exact-match rate and
  protected route preservation. It does NOT claim factual verification.

## Windows

```powershell
git fetch origin
git switch --track origin/v0.7.14
python -m unittest -v test_multi_candidate_audit_v0714.py test_candidate_response_validation_v0713.py test_candidate_aware_fallback_v0712.py
python run_multi_candidate_audit_v0714.py --unknown "未登録の対象とは"
```

The experiment uses files `data/approved_v071.jsonl` and
`data/candidates_v071.jsonl`. If only the prior v072 candidate is
registered, the real GPU audit contains **one** candidate; the six new
unit tests supply three isolated sample candidates to test multi-record
behavior. To measure three or more *learned* facts, train the adapter
against the same Candidate dataset (see v0.7.9), then supply its matching
checkpoint. Simply adding a Candidate Memory record without training
does not imply the adapter knows it.

Protected retention here is a **routing invariant**, not a measured
knowledge-retention or factual-accuracy score. All outputs remain
experimental and no auto-promotion occurs.
