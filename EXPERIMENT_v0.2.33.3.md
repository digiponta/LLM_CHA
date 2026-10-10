# LLM_CHA v0.2.33.3 — Semantic Consistency Training

Goal: determine whether a meaning-conditioned bridge can distinguish two **different purpose structures** while learning the correct response. This is an ablation, not evidence of full semantic internalization.

## Objective

The frozen base LLM is shared; both arms train only the 64→256 linear projection with identical initial weights and number of optimizer steps.

```text
L = NLL(answer | prompt, correct_semantics)
    + lambda * softplus(margin
                       + NLL(answer | correct_semantics)
                       - NLL(answer | incorrect_semantics))
```

The second term penalizes a wrong-purpose condition making the *same* gold answer as probable as the correct-purpose condition. Negative examples come from records with different purpose lists, avoiding trivial same-purpose comparisons.

- Baseline uses lambda=0; contrastive arm uses lambda=1 by default.
- The gap `wrong_semantic_nll - correct_semantic_nll` is a training-set measure only.
- The current answer/purpose pairs are highly correlated; this can teach superficial purpose discrimination, **not** factual correctness or independent semantic understanding.
- This version focuses on LM + semantic discrimination. Dedicated response retention KL and learner-estimated semantic labels are future work, **not implemented**.
- The training implementation uses only the existing approved six Semantic Memory examples; no synthetic ground truth is added.
- At evaluation, correct semantic labels are supplied externally and relation is not supplied, as in v0.2.33.2. Raw input mode therefore means no *text* DSS prompt, **not** autonomy from DSS.

## Run (PowerShell)

```powershell
git fetch origin
git switch v0.2.33.3
git pull origin v0.2.33.3
python -m unittest -v test_semantic_consistency_v02333.py
python semantic_consistency_training_v02333.py train --steps 72
python semantic_consistency_training_v02333.py evaluate
```

Outputs:
- `model/semantic-consistency-baseline-v02333.pt`
- `model/semantic-consistency-contrast-v02333.pt`
- `results/semantic_consistency_train_v02333.json`
- `results/semantic_consistency_eval_v02333.json`

No existing checkpoint is overwritten, no DSS runtime routing is changed, no automatic promotion is performed. Compare correctness, purpose fidelity, fluency and retention manually; inspected probes are not an untouched independent benchmark. A positive training gap alone is insufficient.
