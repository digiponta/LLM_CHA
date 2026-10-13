# LLM_CHA v0.4.28.2 — Diagnostic Regression and Benchmark Preparation

Scope: `v0.4.0` branch only; no changes to `main`, `chat.py`, `/sleep`, Truth Gate, model, or Semantic Memory.

## Regression alignment
Invalid diagnostic agreement scores now return a read-only warning and `INVALID_DIAGNOSTIC_SCORE` flag instead of raising during shadow evaluation. The historical `test_bad_scores` test now checks this policy. The `accepted` argument still requires a boolean.

## Benchmark manifest
`prepare_chat_benchmark_v04282.py` consumes the v0.4.28 development benchmark TXT, skips all comment/heading lines, validates 52 SINGLE and 12 MULTI prompts, groups four three-turn conversations, and refuses overwriting a preexisting output.

This is **manifest preparation only**. It does not automate chat inference or claim model accuracy. Follow-up evaluation automation must record full routes, including retrieval/fixed persona, runtime state, model SHA, and consent/privacy boundaries.

The current benchmark has already been viewed during development and is **not** an independent holdout. Do not use it for training.

## Windows commands

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_persona_relevance_hardening_v04281.py test_persona_response_shadow_v0421.py test_prepare_chat_benchmark_v04282.py
python verify_integration_v0366.py --gpu --legacy --timeout 240
python prepare_chat_benchmark_v04282.py --input llm_cha_chat_benchmark_v0428.txt --output results/chat_benchmark_manifest_v04282.json
```

Place the previously supplied benchmark TXT in the repo root first, or replace --input with its actual location. `--output` must be a new path. Do not copy comments into `chat.py`.

Next: implement explicitly opt-in, read-only candidate inference capture from an isolated checkpoint using manifest groups and verifiable run metadata. Do not use `/sleep` on the active checkpoint solely for evaluation.
