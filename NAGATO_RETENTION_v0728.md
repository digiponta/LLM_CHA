# LLM_CHA v0.7.28 — Nagato 11-Candidate Retention Audit

Read-only evaluation of the Experimental LLM's old one-record checkpoint
and its new eleven-record checkpoint. No new training or promotion.

Prepare fixed probes using both checkpoint candidate ID sets and the
current PENDING store, preserving source IDs. Each candidate receives
the exact line-recall question it was trained on. Compute raw greedy
generation against both checkpoints and compare the old and new cohorts.
The old-cohort forgetting rate is the fraction of initially correct old
questions that are wrong in the later checkpoint. A zero denominator
is reported as null, not zero. SHA-256 input hashes are checked before
and after inference.

## Windows PowerShell

```powershell
git fetch origin
git switch --track origin/v0.7.28
python -m unittest -v test_nagato_retention_v0728.py test_longitudinal_v0726.py

$old="results/experimental_sleep_v0722/experimental-sleep-88c3cbc845c6ff0d0973.pt"
$new="results/experimental_sleep_v0722/experimental-sleep-0f899c7fbf272acee304.pt"

python prepare_nagato_retention_v0728.py --old $old --new $new
python benchmark_nagato_retention_v0728.py --old $old --new $new
```

Expected report location:
`results/nagato_retention_v0728/report.json`.

The Nagato corpus was imported as line-number QA. These tests measure
**reproduction of the specific trained text**, not natural language
generalization or scientific factual truth. To test questions like
“宇宙とは” or “時間とは”, add independently authored paraphrase probes
and compare their exact/semantic response quality separately.
The Trusted checkpoint is not loaded for modification in this audit.
