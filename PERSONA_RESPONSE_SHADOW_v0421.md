# LLM_CHA v0.4.21 — Persona Response Quality Shadow Evaluation

Shadow-only instrumentation of normal generation in `chat.py`; neither rewrites answers nor changes Truth Gate, ranking, semantic memory, Wiki, training or acceptance. Currently configured for Nagato profile.

`persona_response_shadow_v0421.evaluate` reports the existing runtime accept decision alongside rule-based warning flags:
- AGREEMENT_DIVERGENCE: probe agreement below 0.35 while semantic agreement >= 0.82. **Review-only, not an error**: "今日は何をしていたの → 特に変化はない。" is a valid counterexample.
- OUTPUT_FRAGMENT_MARKERS: suspicious pipe / truncated excerpt markers.
- IDENTITY_MISMATCH: identity question without "長門有希".
- ABSTENTION / EMPTY_ANSWER: no response.

The flags are intentionally not used as classifier accuracy or estimated answer correctness. Independent gold-labelled holdout and precision/recall/false rejection measurement are **not yet available**. Do not tune thresholds or infer accuracy from these synthetic cases. Existing v0.4.13 holdouts are not independent for tuning.

## Run on Windows

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_persona_response_shadow_v0421.py test_persona_dialogue_intent_v0420.py test_persona_identity_guard_v0419.py
python verify_integration_v0366.py --gpu --legacy --timeout 240
python chat.py
```

Try "今日は何をしていたの", "貴方は誰", "長門", "化学とは", "CPUとは". The runtime answer must remain unchanged. A [persona-shadow=REVIEW] is diagnostic only and may flag an acceptable answer.
