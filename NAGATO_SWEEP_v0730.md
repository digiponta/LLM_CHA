# v0.7.30 — Nagato Experimental Generation Length Sweep

Measures 32, 64, 128, 256 generated-token budgets using the **same**
Experimental Adapter learned in v0.7.27. No training, promotion or
Trusted-model writes.

For each of the Nagato PENDING Candidate records, report target BPE
token count, full exact match, initial matching BPE token count,
prefix ratio, generated-token count and wall-clock time.

Important: v0.7.29 found **8/10** answers too long for 32 tokens and
**0/10** exact matches. The sweep can show whether extending generation
improves exact reproduction; it cannot prove factual knowledge or
generalization. If prefix accuracy is low at every budget, examine
teacher-forced target NLL and training alignment next.

## PowerShell

```powershell
git fetch origin
git switch --track origin/v0.7.30
python -m unittest -v test_nagato_sweep_v0730.py test_nagato_length_v0729.py
python sweep_nagato_generation_v0730.py `
  --adapter results/experimental_sleep_v0722/experimental-sleep-0f899c7fbf272acee304.pt
```

Report: `results/nagato_sweep_v0730/report.json`.

The script checks the checkpoint Candidate ID set and SHA-256 input
hashes, and skips Approved JSONL if absent (valid empty store). It does
not alter Semantic Memory or model weights. It performs 40 generations
for ten Nagato records (four budgets each), so this diagnostic is more
computationally expensive than a single 32-token benchmark.
