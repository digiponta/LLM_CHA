# LLM_CHA v0.2.28.2 — EOS / Continuation Probability Analysis

**Status:** Diagnostic implementation ready; local GPU results pending. No training.

## Objective
v0.2.28.1 showed inadequate self-generated continuation after a correct
response prefix. Separate early EOS selection from weak semantic continuation
and the effect of deterministic decoding.

## Arms
- `greedy`: standard argmax with repetition penalty 1.15
- `no_eos_16`: disallow EOS for steps 0–15 (zero-based)
- `no_eos_32`: disallow EOS for steps 0–31
- `sample_topk`: temperature 0.8 / top_k 40 with seed 42

Per step, record raw post-repetition-penalty EOS probability/rank, original
top-1, chosen token, and whether EOS was suppressed. The EOS probability is
measured *before* suppression.

## Run
```powershell
git fetch origin
git switch v0.2.28.2
python -m unittest -v test_eos_continuation_v02282.py
python diagnose_eos_continuation_v02282.py
```

Output: `results/eos_continuation_v02282.jsonl`. There are 3 checkpoints ×
3 topics × 2 prompt formats × 4 arms = 72 conditions. The output includes
all token traces and summaries.

## Interpretation
- EOS suppressed and generation becomes coherent: early EOS likely contributes.
- EOS suppressed but repetition / malformed text increases: token selection and
  language modeling, not only EOS, need investigation.
- Top-k materially improves grounded continuation: decoding strategy matters,
  but replicate across seeds before concluding.
- All arms fail: likely requires stronger training data/architecture or
  objective changes; investigate in v0.2.29.

A longer text isn't automatically a better response. Do not equate EOS
suppression with improved semantic grounding. No multi-seed or broad holdout
generalization claim should be made from this limited diagnostic.
