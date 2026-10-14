# LLM_CHA v0.4.28.29 — Tiny Cross-Encoder Weak-Supervision Experiment

This experiment trains an isolated 2-layer, 64-dimension PyTorch Transformer encoder on `[question, answer]` pairs with shared hashed-character embeddings, segment and position embeddings, and a scalar relevance head. It is deliberately lightweight for CPU/RTX 3070 Ti and requires local PyTorch. It does **not** reuse the LLM_CHA generation model and downloads no pretrained models.

**Crucial limitations:** 64 already-inspected development cases only; 63 ChatGPT weak labels (10 positive / 53 negative, one uncertain excluded). Training and predictions use the same 64 examples. The output `diagnostic_uncalibrated_probability` is **an uncalibrated in-sample training diagnostic, not generalization accuracy**. The formal protocol emits `ABSTAIN` for all predictions because no defensible threshold or independent holdout is established. No Truth Gate deployment, model replacement, or other runtime modifications.

PowerShell:

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m py_compile train_qa_cross_encoder_v042829.py
python -m unittest -v test_train_qa_cross_encoder_v042829.py test_semantic_qa_model_contract_v042828.py

python train_qa_cross_encoder_v042829.py `
  --validation results/semantic_probe_validation_v042812.json `
  --labels results/chatgpt_qa_labels_v042823.json `
  --epochs 30 `
  --device cuda `
  --output results/qa_cross_encoder_experiment_v042829.json
```

Use `--device cpu` when CUDA is unavailable. Output includes input hashes, training loss, protocol-compliant `ABSTAIN` predictions and uncalibrated diagnostic scores. Output will not overwrite existing files. There are 5 new tests (4 pure encoding tests and 1 PyTorch one-epoch smoke test); 6 prior contract tests. Verification on user's machine pending.

Next: collect *unseen* QA answer pairs with human adjudication, keep a separate test set untouched, improve representation (a pretrained multilingual model is a candidate but needs explicit dependency/network decisions), and evaluate before calibrating relevance decisions. Preserve provenance, /sleep, Semantic Memory, Truth Gate, chat.py and model checkpoints.
