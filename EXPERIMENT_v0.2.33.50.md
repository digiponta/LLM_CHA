# LLM_CHA v0.2.33.50 — Reference Expiration & Stale Confirmation Safety

This experimental `ExpiryGuardBridge` adds a candidate validity check immediately before confirming natural-language "はい"/"いいえ": verifies the current pending ID exists, record is pending and context matches, candidate has not reached its absolute expiration time, and a configured number of confirmation turns has not elapsed. On expiry, it rejects the outstanding candidate and returns `expired` rather than promoting stale data.

The clock is deterministic and injected into the experimental `JsonCandidateStore`. Six diagnostics cover approval just before a one-hour expiry, refusal just after expiry, replay of assent, unrelated context, a topic switch after choosing a candidate, and a maximum confirmation-turn policy.

**Important limitations:** This is a test adapter, not an update to the production `chat.py`. It does **not** prove atomic multi-process race safety, nor does it address stale-approval requests carrying old candidate IDs when a newer confirmation is pending. The JSON shadow store is not the production Semantic Memory. The evaluations are handcrafted; the recorded results must be executed on the target Windows environment.

## PowerShell

```powershell
git fetch origin
git switch v0.2.33.50
git pull origin v0.2.33.50
python -m py_compile reference_expiration_v023350.py
python -m unittest -v test_reference_expiration_v023350.py test_natural_confirmation_lifecycle_v023349.py
python reference_expiration_v023350.py
```

Produces `results/reference_expiration_v023350.json` and refuses overwrite.

## Next

Investigate stale **candidate-ID** confirmations and concurrent refresh, add atomic compare-and-swap semantics for approvals, and keep natural-language yes/no scoped to the active confirmation context before integrating into any real runtime.
