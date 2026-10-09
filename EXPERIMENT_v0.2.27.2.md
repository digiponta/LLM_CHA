# v0.2.27.2 Diagnosis → v0.2.28 Decision Gate

Status: v0.2.27.2 implementation ready; no user GPU results yet.

## Diagnostic setup
Run:
```powershell
python -m unittest -v test_initiation_distribution_v02272.py
python analyze_initiation_distribution_v02272.py
```
Three frozen checkpoints are compared on the same tokenizer and prompts:
- v0.2.27 standard SFT
- v0.2.27 all-example initiation
- v0.2.27.1 context-selective initiation

Each prompt is evaluated in single-turn and the exact synthetic v0.2.25-style conversation layout.
The first teacher target token is measured directly from the raw next-token probability
distribution. The measured rank/probability is **not** a semantic-grounding metric:
byte-level BPE may split Japanese into subword or byte fragments. Copying a topic
string is not proof of topic understanding.

## Interpret before changing training
- Training-form boost: if target probabilities/ranks materially improve in
  training_format but not single, investigate prompt/context format mismatch.
- Weak top token: if both forms keep target far below top-1, investigate
  contextual supervision and the role of common openers.
- Only initial change: if first-token scores improve but continuation does not,
  design v0.2.28 Context Persistence Learning.
- Inconclusive: add independent prompts/seeds and teacher-forced multi-position
  NLL tests before attributing causation.

## Proposed v0.2.28 (NOT YET VALIDATED)
- Keep v0.2.27.1 checkpoint frozen as an experimental comparator.
- Add response-position-specific *middle/late* token loss, restricted to
  provenance-tagged context examples, rather than increasing all-example SFT.
- Test three arms: existing baseline, initiation-only, initiation+middle/late.
- Define response phases using assistant-only mask and relative token positions;
  prevent prompt/padding from receiving auxiliary loss.
- Evaluate raw greedy continuation under exactly matched prompts, complete
  semantic topicality, word/phrase repetition, EOS behavior, unknown-topic
  holdouts, everyday conversation, and persona preservation.
- Apply the same model source, steps, data exposures, optimizer, seed,
  decoding and prompt policy to all controlled arms.
- Do NOT train v0.2.28 until the v0.2.27.2 diagnostic results have been
  reviewed and a failure mode has been selected. No performance claims now.
