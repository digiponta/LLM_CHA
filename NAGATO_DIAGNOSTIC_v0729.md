# LLM_CHA v0.7.29 — Nagato Long-Answer Diagnostic

This version adds a non-training diagnostic for the ten imported Nagato
PENDING Candidate records. It checks:

- BPE token count for each reference answer and question prompt.
- Whether the answer exceeds the **actual 32-token ExperimentalBackend**
  generation limit.
- Whether prompt plus reference exceeds the Base model's 512-token window.
- Raw generated prefix agreement (token IDs), exact answer match, and
  previews of expected and generated text.

Importantly, the previous 0/10 exact result can reflect truncation,
poor memorization, or both. An answer longer than 32 tokens is impossible
to reproduce in full by the current 32-token generator. No inference
of effective training can be made solely from this length check.

This diagnostic deliberately does not claim to measure Target NLL.
Teacher-forced NLL across masked targets requires a separate evaluation
with precisely matched training prompt formatting. It also does not
modify Approved Memory, Candidate status, Base or Trusted weights.

## Windows PowerShell

```powershell
git fetch origin
git switch --track origin/v0.7.29
python -m unittest -v test_nagato_length_v0729.py
python diagnose_nagato_length_v0729.py `
  --adapter results/experimental_sleep_v0722/experimental-sleep-0f899c7fbf272acee304.pt
```

Report: `results/nagato_diagnostic_v0729/report.json`.
Expected count is ten Nagato PENDING records from the prior import;
the earlier experimental Candidate is not included in this diagnostic.
