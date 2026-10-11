# LLM_CHA v0.2.33.53 — Session Reference Memory Runtime Stabilization

## Objective

Validate the **real opt-in adapter** introduced in v0.2.33.52 across restarts, expiry, context isolation, interruption, cancellation and unchanged ordinary conversation. The default `chat.py` behavior and existing factual Semantic Memory are intentionally not altered.

The session reference DB is `data/session_reference_memory.sqlite3` by default. This is **a separate persistent reference namespace**, not the semantic proposition store or model-internalized knowledge.

## Verification

```powershell
git fetch origin
git switch v0.2.33.53
git pull origin v0.2.33.53

python -m py_compile chat.py runtime_reference_integration_v023352.py session_reference_stabilization_v023353.py
python -m unittest -v test_session_reference_stabilization_v023353.py test_runtime_reference_integration_v023352.py test_atomic_confirmation_v023351.py test_reference_expiration_v023350.py
python session_reference_stabilization_v023353.py
```

Produces `results/session_reference_stabilization_v023353.json` (refuses overwrite). Thirteen diagnostics cover: initial approval, approved lookup after simulated process restart, context B isolation, ordinary chat fallthrough, no orphan yes after restart, persistent invalidation, abandoned pending candidate after restart, expiry boundary, purpose switch, cancel+delayed yes, ambiguous assent, stale candidate ID and Japanese confirmation rendering.

## GPU-backed interactive smoke test

```powershell
python chat.py --session-reference-memory --session-reference-context manual-v023353
```

Suggested manual dialogue: `昨日の実験の続きをやって`, `カーソルでお願いします`, `はい`, `/refstatus`, `/exit`; restart with the **same context and DB**, input `前回の実験を再開して` to test persisted reuse. Also try `/refinvalidate`, `/reset`, `キャンセル`, a DSS switch, and an unrelated question; confirm that the unrelated question still reaches ordinary chat generation. Be aware the initial ambiguous reference classification is a narrow deterministic MockDSS-based rule.

### Boundaries

- This is **not merged into main**. Enable with `--session-reference-memory`.
- Approved references survive restart while their TTL remains valid. **Pending conversational state is not restored**: orphan `はい` is intentionally not approved.
- The reference DB is isolated from Semantic Knowledge Architecture, semantic propositions, /sleep and model weights. Conflating ephemeral pointer/reference data with long-lived verified facts would be unsafe.
- Researcher-authored diagnostics are not independent natural-language generalization evidence.
- Multi-process crash recovery, lifetime of dangling pending rows, cross-device time consistency and GPU-level manual interaction remain separate validation.
