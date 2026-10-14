# LLM_CHA v0.4.28.30 — Checkpoint and grouped internal holdout

Adds a standalone PyTorch 2-layer 64-dimensional QA Cross-Encoder experiment (no changes to live Truth Gate, LLM_CHA weights, Semantic Memory, /sleep, /train or chat.py). The model is trained **only on the training partition**, with a deterministic ~20% *question-grouped* internal holdout, excluding null provisional labels. This prevents exact normalized-question overlap across train and holdout, but does NOT prove semantic independence, domain generalization, or external test accuracy.

ChatGPT labels are weak provisional supervision, not human labels. Scores are uncalibrated and not thresholded; all decisions remain ABSTAIN. The experiment saves its training checkpoint and reloads it using `torch.load(..., weights_only=True)`; scores before and after reload must match. Unlike v0.4.28.29 this run trains afresh from seed and does **not** convert an existing v0.4.28.29 in-memory model into a checkpoint. Therefore compare losses only with care.

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m py_compile evaluate_qa_cross_encoder_v042830.py
python -m unittest -v test_evaluate_qa_cross_encoder_v042830.py test_train_qa_cross_encoder_v042829.py

python evaluate_qa_cross_encoder_v042830.py `
  --validation results/semantic_probe_validation_v042812.json `
  --labels results/chatgpt_qa_labels_v042823.json `
  --epochs 15 `
  --device cuda `
  --checkpoint model/qa_cross_encoder_v042830.pt `
  --output results/qa_cross_encoder_holdout_v042830.json
```

Output includes per-case train/internal-holdout uncalibrated scores, labels, checkpoint SHA-256, partition sizes, and verified checkpoint round-trip. Both output paths must not exist before the run. `--device cpu` is supported. The five new tests include one train/reload smoke test; Windows verification is pending.

Next step: obtain new external question/answer pairs with reliably adjudicated labels, check normalization/group leakage and label imbalance, and measure held-out metrics with uncertainty intervals before considering calibration or deployment.
