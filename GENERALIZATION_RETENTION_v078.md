# LLM_CHA v0.7.8 — Paraphrase Generalization and Approved-Retention Benchmark

This offline benchmark compares three selected v0.7.7 checkpoints on five
manually authored **untrained question strings** and any explicitly approved
knowledge available in the v0.7.1 Approved Memory.

Default checkpoint candidates:
- Rank 8 / Epoch 100 / LR 3e-4
- Rank 16 / Epoch 30 / LR 1e-3
- Rank 32 / Epoch 30 / LR 1e-3

The default questions are paraphrases of the single experimental
`v072実験の合言葉は何ですか` candidate. Answer text remains the same as
the training target. This is a paraphrase generalization probe, **not**
a held-out fact or proof of independent knowledge acquisition.

## Windows

```powershell
git fetch origin
git switch --track origin/v0.7.8
python -m unittest -v test_generalization_v078.py test_adapter_sweep_v077.py

python benchmark_generalization_v078.py `
  --report results/generalization_retention_v078.json
```

Inspect `results/generalization_retention_v078.json` for every raw generated
answer and exact-match result.

Alternative manually reviewed holdout list:
```json
[
  {"question":"v072実験の合言葉を教えてください","reference":"候補の実験回答です。"}
]
```
Run with `--holdouts path/to/holdouts.json`. The code rejects exact matches
to any PENDING training question and duplicate holdout questions. It does not
yet reject near-duplicate text or semantic leakage: human review remains
necessary.

## Retention and quality

If the Approved Memory contains zero records, `retention.exact_match` and
`quality_pass` are `null`. **Do not approve fabricated experimental facts**
merely to satisfy the retention requirement. For robust retention testing,
assemble a separate, verified and suitably varied protected QA benchmark.

If Approved data exists, the benchmark compares Base to Experimental exact
matches on Approved QA and tests holdout improvement. Passing this limited
comparison is **not deployment authorization**.

No model training, adapter modification, production routing or knowledge
promotion is performed. The v0.7.7 sweep already selected the checkpoints
using in-training QA results, so this benchmark is exploratory, not a final
independent test.
