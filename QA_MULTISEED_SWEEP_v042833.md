# LLM_CHA v0.4.28.33 — Multiseed Internal Development Robustness

Repeat the v0.4.28.30 PyTorch QA Cross-Encoder training with five seeds. Each seed **changes the group-based train/holdout split, initialization and training order**. Thus the observed AUC distribution combines split difficulty and stochastic training differences; it is NOT a controlled initialization-only comparison.

Every seed writes a fresh checkpoint and verifies reload agreement. Per-run report includes train count, holdout positive/negative class distribution, Positive×Negative pair count, internal weak-label ranking AUC (null if one class absent), and checkpoint hashes. Means/min/max include only defined AUCs and display undefined count. The dataset is the same previously inspected 64-case development corpus, with 63 weak ChatGPT labels; it is neither external held-out evidence nor a human-verified performance benchmark.

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m py_compile sweep_qa_multiseed_v042833.py
python -m unittest -v test_sweep_qa_multiseed_v042833.py test_inspect_qa_ranking_failures_v042832.py

python sweep_qa_multiseed_v042833.py `
  --validation results/semantic_probe_validation_v042812.json `
  --labels results/chatgpt_qa_labels_v042823.json `
  --epochs 15 `
  --device cuda `
  --checkpoint-dir model/qa_multiseed_v042833 `
  --output results/qa_multiseed_v042833.json
```

Expected focused tests: 9 (4 new + 5 previous), not yet Windows verified. A run is intentionally stopped if any per-seed checkpoint already exists; use a fresh output and checkpoint directory on rerun. Note: a mid-sweep failure may leave valid per-seed checkpoint files but no summary report. No changes to live Truth Gate, generator weights, Semantic Memory, /sleep, /train, or chat.py.

Next: review AUC variance and class counts first. Then to isolate model-initialization sensitivity, introduce a fixed partition with controlled multiple initialization seeds. External separately labeled data will still be required before deployment claims.
