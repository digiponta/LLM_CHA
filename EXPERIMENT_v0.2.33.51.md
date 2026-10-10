# LLM_CHA v0.2.33.51 — Atomic Confirmation & Candidate Version Safety

This branch introduces a **separate SQLite transactional research prototype**. Each candidate is assigned a unique ID and a monotonically increasing version within its `(context, subject, slot)` key. Under SQLite `BEGIN IMMEDIATE`, `propose` supersedes pending candidates and advances the version. `transition` only accepts an exact current ID/version/context in `pending` status. Each transition commits atomically, so replayed approvals, stale candidate IDs, and rejected or expired candidates cannot change to approved through this API.

Seven diagnostics: stale version, double approval, cross-context, reject terminality, expiry terminality, two-thread simultaneous confirmation, and replacement of a candidate. This is NOT a full concurrency stress test; threads use separate SQLite connections, and there is no process-level adversarial test or application-layer exactly-once delivery guarantee.

## Windows PowerShell
```powershell
git fetch origin
git switch v0.2.33.51
git pull origin v0.2.33.51
python -m py_compile atomic_confirmation_v023351.py
python -m unittest -v test_atomic_confirmation_v023351.py test_reference_expiration_v023350.py
python atomic_confirmation_v023351.py
```
Output: `results/atomic_confirmation_v023351.json`, refuses overwrite.

## Limitations and next steps
The store intentionally **does not replace** `JsonCandidateStore`, nor does it integrate with `chat.py`, production Semantic Memory, or v0.2.33.50's fake-clock TTL policy. Revision numbers are scoped to the same semantic key; user-facing confirmations must retain the exact issued ID and version. Durable invariants must be tested under multi-process load, crashes, candidate TTL, and superseding an **already approved** record before integration. An old approved record may remain queryable via `approved()` in this prototype; it is not a production authority for the latest reference. No LLM parameters are modified.
