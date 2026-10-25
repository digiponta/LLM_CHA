# LLM_CHA v0.9.7.17 — Extreme Disagreement Gate & Dialogue Diagnostics

## Purpose
In a real trace the checkpoint generated nonsensical text but the runtime
accepted it because `semantic_agreement=0.854` despite
`lexical_agreement=0.017`. Semantic similarity alone must not override
catastrophic probe disagreement.

## Changes
- Gate rejects *semantic rescue* when lexical probe agreement is below
  a provisional floor of **0.05**. Standard lexical agreement acceptance
  is unchanged.
- Diagnostic command `/clipboard-dialogue-status` displays transient
  category/taste state without exposing clipboard text or product names.
- Existing short-lived taste dialogue is unchanged.

The 0.05 floor is an experimental guard, not a calibrated scientific
threshold. It may reject legitimate paraphrases; run regression benchmarks
on held-out general and factual questions before integrating to main.
It does not detect all malformed Japanese and is not a semantic truth gate.

## Windows verification
```powershell
git fetch origin
git switch --track origin/v0.9.7.17
python -m unittest -v test_extreme_probe_disagreement_v09717.py test_clipboard_taste_dialogue_v09716.py test_clipboard_dialogue_intent_v09715.py
python chat.py
```

Then manually read a Starbucks menu and submit the experience report:
```text
/read-clipboard
ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver.を飲んだことがある
/clipboard-dialogue-status
酸味と甘さのバランスが良かった
/clipboard-dialogue-status
黒耳は、ブラックチョコレートで甘かった
/clipboard-dialogue-status
```
Expected taste turns: 2 -> 1 -> 0. The status command does not
consume a taste turn. If a response still enters `MODEL_GENERATION`,
inspect the utterance and source-product exact matching.
