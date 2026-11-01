# RSE Gate Benchmark v0.13.58.83.06

Adds a diagnostic benchmark for both rejected unsuitable answers and mistakenly rejected suitable answers. The six included cases are synthetic/reused development checks; **not independent holdout**. A manual-review decision is an abstention and must never be counted as a successful accepted response.

PowerShell:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.83.06-rse-gate-benchmark
python -m unittest -v test_rse_gate_benchmark_v013588306.py test_rse_integrated_v013588305.py
python evaluate_rse_gate_v013588306.py
```

Report: results/rse_gate_benchmark_v013588306.json

Metrics: rejection recall on negative cases, false rejection rate on positive cases, and share still needing manual review. These do not establish false acceptance rate because the current gate has no automatic acceptance path. The existing RSE fallback always proposes a conservative answer for conversational intents; this benchmark does not evaluate its naturalness.

Next evaluate additional truly unseen, human-judged positive and negative candidate pairs. Do not switch on automatic response acceptance or model expansion based solely on these development cases. No chat.py/model changes.
