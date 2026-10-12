# LLM_CHA v0.2.34.1 — Context Restore Validation

Status: **Experimental / opt-in module**, not integrated with `chat.py`.
Branch: `v0.2.34-longterm-context`. Stable release `v0.2.33.82` remains unchanged.

## Security and semantics
- `ContextCheckpoint.restore` first validates snapshot schema.
- Caller supplies a **fresh** authoritative corpus mapping `subject -> CurrentSubject`, containing proposition statements, exact provenance, current subject Truth State and subject Gate allowance.
- `validate_restored_context` recomputes IDs and calls the existing `TruthOverlay.decide` for every corpus candidate.
- A saved ID survives **only** when it matches an authorized, current corpus proposition. Missing subjects, changed statement or provenance, and FALSE/OUTDATED/CONTESTED or blocked subject states fail closed.
- A proposition-level TRUE overlay cannot override a blocked subject.
- UNVERIFIED survives only when the subject gate allows it; any displayed answer must still carry a warning in the presentation layer.
- Duplicate IDs within current corpus are conservatively rejected.
- The active topic is preserved only if it retains at least one authorized proposition; otherwise it becomes `None`.
- No file writing, auto-promotion, synthesis or model-weight modification.

## Tests

```powershell
git fetch origin
git switch v0.2.34-longterm-context
git pull --ff-only origin v0.2.34-longterm-context
python -m unittest -v test_longterm_context_v02340.py test_context_restore_validation_v023341.py
```

Expected 8 existing + 11 new tests = **19 tests**. These are **not yet user-executed**.

## Next
Integrate a read-only reconstruction adapter with real current corpus and existing subject truth gate. Never treat restored history as an authorization token. Preserve baseline regressions and GPU acceptance checks before turning any feature on by default.
