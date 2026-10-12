# LLM_CHA v0.3.6.3 — Opt-in Minimal Active Topic Retention

Experimental development branch: `v0.3.0`; stable `main` / `v0.2.34` unchanged.

## Scope
The new `ActiveTopicContext` subclasses `MultiTopicContext` and preserves its public routing interface, TTL and explicit topic resolution. It changes eviction from pure LRU to least-observed-frequency (with recency/first-turn/tie-breakers); explicit pins are never evicted automatically. A fully protected cache rejects admission, and the ConversationTopicAdapter returns `NO_TOPIC` before entering Truth Gate for rejected explicit topics. Only topic metadata is affected, not knowledge or model parameters.

IMPORTANT: This minimal runtime policy is **not yet the full v0.3.5 adaptive importance/auto-pin policy**. It does not infer importance, preserve v0.3.5 auto-pin budgets, or guarantee improved topic return rate. Until tested on GPU and broader heldout, do not treat it as a stable active policy.

## Feature flags
```powershell
$env:LLM_CHA_MULTITOPIC="1"
$env:LLM_CHA_RETENTION_ACTIVE="1"
$env:LLM_CHA_RETENTION_PINS="宇宙,GPU" # optional protected names
Remove-Item Env:LLM_CHA_CONTEXT_RECOVERY -ErrorAction SilentlyContinue
python chat.py
```
Default ACTIVE=0 retains the original runtime. `/retention-stats` prints active diagnostics when enabled. The shadow flag is independent but is only diagnostic.

For v0.3.6.3, active context and Context Recovery cannot be combined (`LLM_CHA_CONTEXT_RECOVERY=1` raises an error at startup). This is a deliberate fail-closed restriction until cursor synchronization and truthful restore/admission semantics are tested. Never bypass Truth Gate with retention metadata.

## Validation
```powershell
git switch v0.3.0
git pull --ff-only origin v0.3.0
python -m py_compile chat.py conversation_topic_adapter_v0233822.py active_topic_context_v0363.py
python -m unittest -v test_active_topic_context_v0363.py
python verify_integration_v0362.py --gpu --legacy --timeout 240
```
New tests: **12** (v0.3.6.3) plus previously accepted 233 tests. The existing combined gate intentionally still checks 233; the new 12 are tested separately pending an updated unified gate. Run results must be supplied before claiming PASS.

## Next
Validate OFF versus ACTIVE with GPU transcripts covering 9+ topics, existing truth-state validation, explicit pin, capacity rejection, TTL, `/reset`, and a rejected-topic cursor check. Then implement safe active/checkpoint recovery interactions as a separately gated change.
