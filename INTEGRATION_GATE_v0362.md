# LLM_CHA v0.3.6.2 — Integrated Regression Gate and Active-Mode Safety Contract

Development branch: `v0.3.0`. Stable tag `v0.2.34` / `main` unchanged.

## Integration gate

`verify_integration_v0362.py` loads **233** unit tests in ONE process: 141 existing stable tests and 92 adaptive context/shadow tests. It fails for skipped tests, exceptions, failures or count mismatch. Optional flags launch two previously verified GPU harnesses and the legacy LLM_TRY v10.16.5 conditional runtime regression.

```powershell
git switch v0.3.0
git pull --ff-only origin v0.3.0
python verify_integration_v0362.py --gpu --legacy --timeout 240
```

Expected: `[combined-unit] ... expected=233 ok=True`, successful `RECOVERY_GPU`, `SHADOW_GPU`, `LEGACY`, then `INTEGRATION_GATE_V0362_PASS`. These are **acceptance targets**, not an already observed run.

## Active Mode safety contract — design only

Do **not** enable Active Mode by default. Before implementing an opt-in active policy:
1. Routing authority remains the existing Conversation Topic Adapter until Active Mode is explicitly requested and individually accepted.
2. Any active eviction must atomically update topic selection/cursor bookkeeping without mutating Corpus, Semantic Memory, Truth State or LLM model weights.
3. Explicit pins must never be removed automatically. If every available slot is protected, fail closed and report why, never silently route to a different topic.
4. A removed topic may only be restored through current authoritative Corpus lookup and Truth Gate / proposition overlay validation, never by trusting a saved topic or old proposition ID.
5. Distinguish a candidate admission denial from a knowledge denial; a policy decision cannot authorize a fact or generate a fallback answer.
6. Capture OFF/SHADOW/ACTIVE comparative traces with metrics and check for stale cursor, topic hallucination, restart replay, and leakage.
7. Roll back to the stable path when the active feature flag is absent or a policy error occurs.

Existing `LLM_CHA_RETENTION_SHADOW` is diagnostic only. This stage does **not** change `chat.py` nor implement Active Mode. GPU fixture Truth States are synthetic; wider real-chat and concurrent corpus mutation cases remain future work.
