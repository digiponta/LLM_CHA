# LLM_CHA v0.4.28.34 — Fixed-Split Multi-Seed Robustness

Fixed the question-grouped development partition while changing training initialization and minibatch order across five training seeds. This is done using a **backward-compatible** optional `split_seed` argument added to `evaluate_qa_cross_encoder_v042830.run` (default remains identical to previous behavior). The runner refuses a fixed Holdout that contains only one provisional class, checks identical train and Holdout ID/turn sets in all runs, and verifies checkpoint save/reload.

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m py_compile evaluate_qa_cross_encoder_v042830.py sweep_qa_fixed_split_v042834.py
python -m unittest -v test_sweep_qa_fixed_split_v042834.py test_evaluate_qa_cross_encoder_v042830.py

python sweep_qa_fixed_split_v042834.py `
  --validation results/semantic_probe_validation_v042812.json `
  --labels results/chatgpt_qa_labels_v042823.json `
  --split-seed 20261014 `
  --epochs 15 `
  --device cuda `
  --checkpoint-dir model/qa_fixed_split_v042834 `
  --output results/qa_fixed_split_v042834.json
```

Expected focused tests: 8 (3 new plus 5 regression), Windows verification pending. Outputs mean/population-SD/min/max internal weak-label AUC over a **fixed** Holdout and per-training-seed checkpoint hashes. Both Positive and Negative must appear in the fixed Holdout; the default split seed is known to have 3 and 10 from previous measurements, respectively. New output/checkpoint paths are required for reruns.

**Limits:** Same 64 previously inspected development examples, ChatGPT provisional labels, only 13 Holdout examples, no confidence interval, no external human-adjudicated testing, no threshold fitting. The experiment isolates initialization/training-order variation at the chosen partition, not data split difficulty. No live runtime changes, no changes to Truth Gate, generator, Semantic Memory, /sleep, /train or chat.py.
