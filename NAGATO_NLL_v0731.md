# LLM_CHA v0.7.31 — Target NLL and First Token Diagnostic

Investigates why the ten Nagato entries have 0/10 exact generations
even with up to 256 output tokens. Uses the original supervised
`ConversationDataset` prompt/answer masking used by Experimental
Adapter training and measures per-record teacher-forced target NLL,
first answer token rank and Top-K for **Base** vs **Experimental**.

This is diagnostic only. Training-target NLL is not held-out
generalization performance and does not certify factual accuracy.
Target NLL uses the training dataset's loss mask (including EOS
where supervised). The Experimental model remains PENDING, with
no promotion. SHA-256 input hashes are compared before and after
inference. No Trusted weights or memory are written.

## Windows PowerShell

```powershell
git fetch origin
git switch --track origin/v0.7.31
python -m unittest -v test_nagato_nll_v0731.py
python diagnose_nagato_nll_v0731.py `
 --adapter results/experimental_sleep_v0722/experimental-sleep-0f899c7fbf272acee304.pt
```

Report: `results/nagato_nll_v0731/report.json`.

Interpretation:
- Experimental lower NLL but poor free generation: teacher-forced
  knowledge increased, but autoregressive decoding/recovery fails.
- NLL unchanged or worse: revisit data formatting, optimization,
  adapter capacity and number of training passes.
- First-token rank weak across many different inputs: likely
  question-conditioned retrieval/selection failure.
