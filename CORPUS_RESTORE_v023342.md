# v0.2.34.2 — Real Corpus Restore Adapter

Experimental branch `v0.2.34-longterm-context`. Stable tag `v0.2.33.82` untouched.

`corpus_restore_adapter_v023342.py` uses actual `retrieval_first_runtime_v1012161.resolve_subject`, `PropositionCursor.split`, and the authoritative `TruthOverlay.decide` via `validate_restored_context`.

Caller MUST provide a fresh `subject_gate(subject) -> (truth_state, permitted)` that implements the existing Truth State lookup and admission logic. This adapter never treats a persisted checkpoint or the corpus itself as proof of truth. The existing `truth_allows_direct_retrieval` denial is also enforced even if the callback mistakenly permits a FALSE/OUTDATED/CONTESTED subject.

The checkpoint contains only proposition IDs and topics. If a statement, provenance, subject, overlay or gate changes, saved presentation history is re-authorized and removed when no longer valid. UNVERIFIED retention is subject to gate permission, and the caller remains responsible for showing the explicit warning when displaying any record.

No production corpus, checkpoint or model is written. No integration with `chat.py` yet.

## Local regression

```powershell
git switch v0.2.34-longterm-context
git pull --ff-only origin v0.2.34-longterm-context
python -m unittest -v test_longterm_context_v02340.py test_context_restore_validation_v023341.py test_corpus_restore_adapter_v023342.py
```

Expected: **29 tests (8 + 11 + 10)**; execution pending on user's Windows Python environment. Test data is isolated via `tempfile.TemporaryDirectory` and is not a scientific ground-truth evaluation.

Next: assess exact runtime gate injection from `chat.py` and opt-in end-to-end recovery.
