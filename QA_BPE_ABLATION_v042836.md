# LLM_CHA v0.4.28.36 — Local BPE Input Ablation

Adds **optional local HuggingFace `tokenizers` JSON BPE** input to the isolated 2-layer/64-dimensional QA Cross-Encoder experiment. It compares BPE vs original Unicode character-hash encoding on the same deterministic question-group train/holdout partition and paired training seeds; uncalibrated weak-label ranking AUC is reported. Model weights are initialized independently each run. Truncation operates on tokens rather than characters, so comparisons are input-pipeline ablations, not an isolated representation-only causal test.

**Important file constraint:** The expected `model/tokenizer-v0.7-bpe.json` does not exist in the checked GitHub `v0.4.0` branch. Provide the path to your local JSON explicitly. The adapter accepts HuggingFace `tokenizers` JSON with `model.type == "BPE"`; a custom JSON file requires a separate, format-specific adapter and will intentionally fail rather than pretending to tokenize correctly. No downloads are performed. Installation of the optional library requires user action.

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m pip install tokenizers
python -m py_compile evaluate_qa_cross_encoder_v042830.py compare_qa_bpe_v042836.py
python -m unittest -v test_compare_qa_bpe_v042836.py test_compare_qa_representations_v042835.py

python compare_qa_bpe_v042836.py `
  --validation results/semantic_probe_validation_v042812.json `
  --labels results/chatgpt_qa_labels_v042823.json `
  --tokenizer ..\\LLM_TRY\\model\\tokenizer-v0.7-bpe.json `
  --split-seed 20261014 `
  --seeds 20261014,20261015,20261016 `
  --epochs 15 `
  --device cuda `
  --checkpoint-dir model/qa_bpe_v042836 `
  --output results/qa_bpe_comparison_v042836.json
```

The tokenizer path is an **example to verify locally**, not a confirmed file location. If validation reports an unsupported tokenizer format, share its non-sensitive top-level structure and model type before modifying the adapter. The current run backend requires token embedding vocabulary size 259..65536; normal project-size 8000-vocab BPE is within that range.

Expected focused tests: 10 (5 new + 5 previous); Windows execution pending. All cases remain the previously inspected 64-case development set, with ChatGPT provisional weak labels and no independent external holdout. No evidence of quality improvement until experiments run. No active Truth Gate, generator, Semantic Memory, /sleep, /train, or chat.py changes.
