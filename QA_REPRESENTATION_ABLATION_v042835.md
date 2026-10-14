# LLM_CHA v0.4.28.35 — Fixed-Split QA Input Representation Ablation

This experiment compares the existing Unicode-codepoint hash embedding with a new **UTF-8 byte input** using the *same* 2-layer/64-dim Transformer, same question-group Holdout, same weak labels, and paired training seeds. It is **not a BPE comparison**: introducing the project BPE tokenizer requires validating its actual API and vocabulary and is deferred. Byte tokenization changes truncation length versus characters; the results measure an input-pipeline ablation, not a controlled pure embedding substitution.

The existing `evaluate_qa_cross_encoder_v042830.run` receives a backward-compatible optional `encode_fn` callable. Defaults remain unchanged. Each pair runs from scratch and verifies checkpoint save/reload; per-seed AUC and UTF-8-minus-codepoint AUC delta are recorded. All scores are provisional on internal development Holdout with ChatGPT weak labels, never independent accuracy or deployable Truth Gate outcomes.

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m py_compile evaluate_qa_cross_encoder_v042830.py compare_qa_representations_v042835.py
python -m unittest -v test_compare_qa_representations_v042835.py test_sweep_qa_fixed_split_v042834.py

python compare_qa_representations_v042835.py `
  --validation results/semantic_probe_validation_v042812.json `
  --labels results/chatgpt_qa_labels_v042823.json `
  --split-seed 20261014 `
  --seeds 20261014,20261015,20261016 `
  --epochs 15 `
  --device cuda `
  --checkpoint-dir model/qa_repr_v042835 `
  --output results/qa_repr_comparison_v042835.json
```

Expected focused tests: 8 (5 new plus 3 fixed-split regression), Windows verification pending. Use fresh output/checkpoint paths on rerun. The user has not supplied the v0.4.28.34 measurement yet; do not infer relative improvement from prior runs. No change to generator, active Truth Gate, Semantic Memory, /sleep, /train, chat.py, or main branch.
