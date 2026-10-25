# LLM_CHA v0.9.7.28 — Daily Conversation Foundation

**Goal:** teach an eventual SFT experiment how to acknowledge everyday user
experiences before attempting complex free-form semantic generation.

The first version provides **30 hand-curated synthetic training pairs and
12 disjoint holdout paraphrases** across six labels:
POSITIVE, DISAPPOINTMENT, SADNESS, FATIGUE, GRATITUDE, UNCERTAINTY.

Each example records input, short answer, dialogue_act, emotion,
response_strategy and CURATED_SYNTHETIC provenance. It is not grounded in
real conversational logs and does not demonstrate generalization yet.

This branch **does not train the model**, modify chat.py, replace existing
persona responses, or automatically write Semantic Memory. The goal is to
validate labels, safety, data split, and export format before GPU SFT.

## Windows PowerShell

```powershell
git fetch origin
git switch --track origin/v0.9.7.28
python -m unittest -v test_daily_conversation_foundation_v09728.py
python prepare_daily_conversation_v09728.py --out data
```

Expected audit: train_count=30, holdout_count=12, no exact input overlaps.

Exported:
- `data/daily_conversation_train_v09728.jsonl`
- `data/daily_conversation_holdout_v09728.jsonl`
- `data/daily_conversation_audit_v09728.json`

The export's `prompt` uses the existing runtime's `人: ...\nAI: `
structure, but compatibility with the original SFT training code still
requires inspection before any model update.

## Recommended next experiment

Build a small, separate GPU SFT checkpoint with these examples blended
with protected Nagato identity and prior successful QA. Compare exact
and paraphrased response intent, identity retention and unrelated topics
against the untouched baseline. Avoid memorization-only scoring; add
negation, mixed emotion, irony and unseen utterances before claiming
real conversation generalization.
