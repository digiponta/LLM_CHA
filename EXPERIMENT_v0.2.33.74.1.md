# v0.2.33.74.1 — Greeting Quality Hardening

## Observed GPU failure (v0.2.33.74)

`こんにちは` produced a malformed but ACCEPTed response, `こんにちは。元気障で 強く資源、 の後の前に注釈を呈する。`. The former heuristic accepted any greeting-prefixed text shorter than 32 characters.

## Repair

The existing `greeting_repair` now preserves **only a small allowlist of complete, standalone greeting responses** when the model has accepted its candidate; every other standalone-greeting output is normalized to a short deterministic greeting. A mixed utterance such as `こんにちは、宇宙について教えて` remains outside this fallback. The Truth-Aware Corpus Gate remains unchanged.

**Known limitation:** This is a surface-response guard, not better model generation or a multi-intent parser. The original accepted/rejected gate and any review-queue side effects still occur. The allowlist intentionally sacrifices conversational variation to avoid greeting-prefixed nonsense.

## Run in Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.74.1
git pull origin v0.2.33.74.1
python -m py_compile chat.py generated_response_quality_v023374.py
python -m unittest -v test_greeting_hardening_v0233741.py test_generated_response_quality_v023374.py test_truth_aware_corpus_gate_v023373.py
python chat.py --session-reference-memory
```

Manual GPU inputs: `こんにちは`, `こんばんは`, `こんにちは、宇宙について教えて`, `宇宙とは`, `/exit`. Expect `こんにちは。` instead of the recorded malformed answer; expect `宇宙とは` still blocked if UNVERIFIED.

No model weights, Truth State or Semantic Memory records are modified by this branch.
