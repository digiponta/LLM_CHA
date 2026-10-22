# LLM_CHA v0.6.18 — Named Topic Wikipedia Evidence Gate

Routes requests such as `スターバックスの話題` to source-grounded
Wikipedia lookup even if the model otherwise might label them KNOWN.
Does not change the base model or Semantic Memory.

Priority: local indexed subject/verified evidence -> local raw concept
evidence -> named-topic Wikipedia lookup -> existing model/UNKNOWN processing.
A named-topic lookup without usable source or answer yields a confirmation
question instead of unsupported text. Explicitly blocked truth states
remain protected.

```powershell
git fetch origin
git switch --track origin/v0.6.18
python -m unittest -v test_topic_evidence_gate_v0618.py test_raw_concept_evidence_v0615.py
$env:LLM_CHA_AOZORA_ROUTER="1"
python chat_window_v061.py --latest-experimental
```

Manual regression: `スターバックスの話題`, `スターバックの話題`,
`長門`, `時間`, `宇宙`. Wikipedia responses remain
EXTERNAL_UNVERIFIED and are never promoted or trained automatically.

The feature handles named-topic intent; a later version can generalize to
broader questions with calibrated citation-grounded answerability scoring.
