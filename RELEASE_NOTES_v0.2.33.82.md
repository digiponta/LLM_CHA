# LLM_CHA v0.2.33.82 — Stable Release

**Released 2026-10-12.** This release fixes the tested baseline for Multi-Topic Truth-Aware Conversation in LLM_CHA. Merged to `main` via [PR #1](https://github.com/digiponta/LLM_CHA/pull/1), merge commit `79bf8184064db48e555d68202f4ee256b5d1d0de`, Git tag and [GitHub Release](https://github.com/digiponta/LLM_CHA/releases/tag/v0.2.33.82) published.

## Features

- Multi-Topic Context: topic switching, return, TTL, conservative ambiguity handling and `/reset`.
- Grounded Follow-up: source-linked retrieval without unconstrained generation.
- Proposition cursor: ordered, non-repeating propositions and exhaustion fallback.
- Proposition Truth Overlay: deterministic IDs, read-only truth/provenance decisions, blocked FALSE/OUTDATED/CONTESTED records.
- Human-reviewed JSONL entries (operator-supplied evidence/reviewer/reason; no automatic TRUE promotion).
- Mixed-state fixture evaluation and real `chat.py` GPU subprocess acceptance test.
- Opt-in via `LLM_CHA_MULTITOPIC=1` (disabled by default).

## Verification (user-run, Windows RTX 3070 Ti)

| Check | Result |
| --- | --- |
| LLM_CHA regressions, one combined invocation | **94/94 PASS** |
| GPU acceptance checks (real chat.py, isolated corpus copy/overlay) | **8/8 PASS**, exit 0 |
| Legacy LLM_TRY v10.16.5 conditional historical cases | **48/48 PASS** |
| Legacy LLM_TRY stable integration | **6/6 PASS**, `CONDITIONAL_SEMANTIC_RUNTIME_STABLE_V10165_PASS` |

The tested GPU Truth State assignments were synthetic filter-test labels, not a scientific adjudication of the underlying physics claims.

## Known limitations

- The GPU runner isolates a corpus copy and the proposition overlay, **not every runtime support file**. Complete filesystem isolation and long-duration stress testing were not validated.
- Retrieved propositions are not necessarily factually correct. UNVERIFIED remains explicitly marked; operator-supplied TRUE is not automatically evidence-verified.
- Grounded retrieval at 0 generated probe tokens does **not** prove internalization into neural model weights.
- Tests establish behavior in tested fixtures and conditional regression scope, not exhaustive real-world safety or all older subsystem regressions.

## Reproduction

```powershell
python -m unittest -v test_multi_topic_context_v0233821.py test_conversation_topic_adapter_v0233822.py test_multi_topic_chat_runtime_v0233823.py test_truth_aware_chat_integration_v0233824.py test_learning_init_v02338241.py test_grounded_followup_v0233825.py test_grounded_expansion_v0233826.py test_expansion_integration_v0233826.py test_proposition_truth_v0233827.py test_truth_integration_v0233827.py test_proposition_review_v0233828.py test_mixed_state_e2e_v0233829.py test_mixed_state_gpu_accept_v02338210.py
python mixed_state_gpu_accept_v02338210.py --timeout 240
python verify_conditional_runtime_stable_v10165.py
```

Source baseline: `v0.2.33.82`. Future changes should use separate development branches.
