# LLM_CHA v0.13.58.82.54 — Evidence-guided extractive decoding

This branch experiments with **inference-time evidence-grounded extraction** instead of increasing negative-learning strength. Existing production GUI gate and model checkpoints are unchanged. The new `evidence_guided_decoding_v013588254.py` checks the untrusted raw candidate with the existing strict gate. When rejected, it copies complete sentences from the supplied evidence and applies the **same** gate to the copied span. If no suitable span is found, it retains the existing attributed fallback.

**Important limitation:** `ACCEPT_SOURCE_EXTRACT` means exact text overlap with external unverified evidence, not independent truth, formal entailment, or improved raw LLM generation. The experiment does not implement semantic equivalence/entailment, and does not automatically mark paraphrases as verified. Source provenance remains visible. Existing production behavior is not changed without separate review.

## Windows verification

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.54-evidence-decoding
python -m unittest -v test_evidence_decoding_v013588254.py test_evidence_replay_v013588249.py
python compare_evidence_decoding_v013588254.py `
  --evidence-json results/evidence_snapshot_v013588249.json `
  --report aligned=results/evidence_aligned_generation_comparison.json `
  --report prefix=results/prefix_generation_compare_v013588253.json `
  --output results/evidence_decoding_v013588254.json
Get-Content results/evidence_decoding_v013588254.json -Encoding UTF8
```

This is offline replay from prior saved reports, so it does not generate new LLM tokens or change weights. It compares `raw_gate` and `strategy` for each candidate; it does not claim the model itself can answer correctly. Next study should benchmark semantic paraphrases against independent annotated source truth and retention sets.
