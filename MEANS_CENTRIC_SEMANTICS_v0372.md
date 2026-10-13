# LLM_CHA v0.3.7.2 — Means-Centric Semantic Transformation

This experimental feature preserves `MEANS_OF(agent,means,predicate)` and derives a means-centered Japanese causative sentence only when a supported verb pattern provides a known surface form and case particle.

```text
/means 彼は電車によって移動する
AI> 電車は彼を移動させる。
/means 私は数学によって問題を解く
AI> 数学は私に問題を解かせる。
```

Causative particles: `を` for 「移動する」「回復する」, `に` for 「作業する」「問題を解く」「意思を伝える」. Unsupported forms are rejected instead of guessed.

`source` and `semantic` are retained, `attribution=PARAPHRASE_NOT_NEW_FACT`, `factual_truth=NOT_ASSESSED`. These are linguistic transformations of an input claim, not new scientifically verified propositions. The operation has no write path into Persona Semantic Memory or Factual Semantic Memory and does not modify the Truth Gate, checkpoints, or default chat routing.

## Verify

```powershell
git switch v0.3.0
git pull --ff-only origin v0.3.0
python -m unittest -v test_means_centric_semantics_v0372.py
python verify_integration_v0366.py --gpu --legacy --timeout 240
python chat.py
```

Use `/means 彼は電車によって移動する` inside chat. This phase supports a small explicit pattern set rather than general Japanese semantic role labeling; broader transformations need distinct evaluation before enabling automatic Persona Memory indexing.
