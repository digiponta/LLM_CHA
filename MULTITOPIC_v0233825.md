# LLM_CHA v0.2.33.82.5 — Grounded Follow-up

Opt-in `LLM_CHA_MULTITOPIC=1` adds a conservative grounding path for
explicit follow-ups. The active topic is looked up in the existing
subject-keyed corpus memory and checked using the existing
`truth_allows_direct_retrieval` policy.

- HIT and policy allows: return the actual source-grounded answer.
- UNVERIFIED: show a warning, matching the current *allow with warning* intent
  (not a claim of independent verification).
- FALSE/OUTDATED/CONTESTED or no corpus hit: do not unconstrained-generate
  details; return a non-factual fallback.
- `/reset`: still clears context only.
- Original model generation remains available to normal non-followup queries.
- This version may repeat existing corpus evidence rather than truly add
  novel detail; extending or decomposing evidence is future research.

## Test

```powershell
git pull origin v0.2.33.82-multitopic-context
python -m unittest -v test_multi_topic_context_v0233821.py test_conversation_topic_adapter_v0233822.py test_multi_topic_chat_runtime_v0233823.py test_truth_aware_chat_integration_v0233824.py test_learning_init_v02338241.py test_grounded_followup_v0233825.py
$env:LLM_CHA_MULTITOPIC="1"
python chat.py
```

Try: 宇宙について教えて / GPUとは / 宇宙の話に戻って / もう少し詳しく / それについて / /reset / もう少し詳しく / /exit.

Target: existing 38 + new 9 = **47 tests**. The 9 new tests are mostly
static safety/path checks, NOT an actual GPU/Truth State end-to-end proof.
Record observed model output and Truth Gate diagnostics separately.
