# LLM_CHA v0.3.6.0 — Shadow-mode Runtime Integration

Branch: `v0.3.0`. Stable tag `v0.2.34` and `main` unchanged.

## Scope and safety
- `retention_shadow_v0360.py` provides read-only shadow retention observations based on v0.3.5. It never changes the authoritative `MultiTopicContext`, Truth Gate, Proposition Cursor, Semantic Memory or model weights.
- `chat.py` enables shadow mode only if both `LLM_CHA_MULTITOPIC=1` and `LLM_CHA_RETENTION_SHADOW=1`.
- Shadow events are recorded *after* existing topic routing decisions. Shadow outputs never control the real routing or generated answers.
- `/retention-stats` displays JSON diagnostic data only. `/reset` and successful `/context-load` clear shadow observations. Restored history is not assumed to be an observation or trusted as a fact.

## Test locally (PowerShell)
```powershell
git switch v0.3.0
git pull --ff-only origin v0.3.0
python -m unittest -v test_retention_shadow_v0360.py
python -m py_compile chat.py retention_shadow_v0360.py
python -m unittest -v test_adaptive_context_v023350.py test_adaptive_retention_eval_v023351.py test_retention_cross_scenario_v0300.py test_hybrid_retention_v0310.py test_adaptive_importance_v0320.py test_auto_pin_protection_v0330.py test_important_competition_v0340.py test_admission_forgetting_v0350.py test_retention_shadow_v0360.py
```
Expected **86 unit tests** (previous 78 + 8 new), pending Windows validation. No claim of GPU acceptance is made yet.

## Manual shadow session
```powershell
$env:LLM_CHA_MULTITOPIC="1"
$env:LLM_CHA_RETENTION_SHADOW="1"
python chat.py
```
Then enter `宇宙とは`, `GPUとは`, `/retention-stats`, `/reset`, `/retention-stats`, `/exit`. Confirm normal Truth Gate outputs and that only diagnostic counters change.

## Next
- Add subprocess GPU acceptance comparing shadow disabled/enabled transcripts and verifying unchanged Trust/Truth Gate decisions, including restore and reset.
- Only after this shadow equivalence test should policy-controlled eviction be considered.
- Existing checkpoint restore must continue fresh Corpus/Truth State validation.
