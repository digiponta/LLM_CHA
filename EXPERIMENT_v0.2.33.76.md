# LLM_CHA v0.2.33.76 — Automated Integration Policy Benchmark

## Scope

This branch introduces a repeatable **deterministic integration-policy benchmark** of the functions actually imported by `chat.py`:

- Multi-Intent routing (5 scenarios)
- Ambiguous reference clarification (3 scenarios)
- Greeting-output quality (4 scenarios)
- Direct Corpus Memory Truth Gate (6 scenarios)

Total: **18 benchmark scenarios**, plus 6 newly authored unittest cases. The harness runs locally without GPU and produces an inspectable JSON report, avoiding subjective claims of end-to-end accuracy.

It **does not launch `chat.py`**, test model generation, perform real Semantic Memory retrieval, confirm reference targets, or replace manual GPU evaluation. Successful completion therefore means the documented deterministic policy functions behave as expected, **not** that the full conversational system is robust.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.76
git pull origin v0.2.33.76
python -m py_compile integration_policy_benchmark_v023376.py
python -m unittest -v test_integration_policy_benchmark_v023376.py test_multi_intent_reference_v023375.py test_greeting_hardening_v0233741.py test_truth_aware_corpus_gate_v023373.py
python integration_policy_benchmark_v023376.py
```

Output: `results/integration_policy_v023376.json`, with per-scenario `passed`, `expected`, `observed`; exit status 1 if any scenario fails. Running again overwrites the generated report but does not change memory or checkpoints.

GPU real-chat follow-up (manual): `python chat.py --session-reference-memory` then `こんにちは`, `こんにちは、宇宙について教えて`, `宇宙とは`, `昨日の続き`. Compare console traces to the deterministic report. For genuine end-to-end automation, future work must isolate runtime side effects (queues, DBs, GPU generation), define trace capture, and run cases in fresh stateful sessions.

No changes to `chat.py`, model weights, Truth States, Semantic Memory or reference DB.
