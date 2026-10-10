# LLM_CHA v0.2.33.6 — Language Foundation Generalization

Objective: go beyond 14-instance memorization by training several response structures across more topics, checking topic and prompt transfer before attempting to reconnect the Semantic Bridge.

The **base LLM** is trained with response-only SFT and replay. DSS, Semantic Memory, Bridge, their existing files and checkpoints remain unchanged.

## Data and validation design

- Training: eight topics (CPU, GPU, Python, Memory, Network, Database, Sensor, OS), three response structures each; plus 5 procedural domains ×2 forms, for **34 training examples**.
- Validation: two different topics (Compiler, Router), three structures each; plus one different procedure ×2 forms, for **8 validation examples**. Validation uses *new topics*, but **shares response template families**, so this is not an independent structural generalization guarantee.
- Free-generation exploratory holdouts: nine questions, including held-out topics Microphone, Browser, Battery; held-out wordings for seen topics; procedure, context, and text continuation. **No direct training-prompt overlap**. They are provided with the repository and should not be called a sealed final benchmark.
- Early stopping based on validation token NLL and best-checkpoint saving.
- Comparison: frozen original Base vs v0.2.33.5 vs new v0.2.33.6, same greedy decoding.
- Retention replay includes the historical basic replies; no automatic claims of retention or INTERNALIZED.

Only 34 deliberately structured examples remain too few to reliably learn Japanese generation. If results remain weak, expand with a legally usable diverse text corpus and high-quality multi-purpose instruction-response pairs instead of merely repeating epochs.

## PowerShell instructions

```powershell
git fetch origin
git switch v0.2.33.6
git pull origin v0.2.33.6
python -m unittest -v test_language_foundation_generalization_v02336.py
python language_foundation_generalization_v02336.py train --epochs 20 --patience 4
python language_foundation_generalization_v02336.py evaluate
```

Models:
- `model/model-llm-cha-language-generalization-v02336.pt`

Logs:
- `results/language_generalization_train_v02336.json`
- `results/language_generalization_eval_v02336.json`

Note: `evaluate` expects the v0.2.33.5 checkpoint available. Output paths are deliberately new; neither an existing model checkpoint nor a result file should be overwritten.

## Interpretation

- Check train/validation NLL divergence, held-out topic definition, procedure ordering, reference resolution, fluency and whether basic replies regress.
- The presence of the correct topic name in a response does **not** establish definition accuracy or semantic internalization.
- The next experiment should reuse the improved base for a **new** Bridge checkpoint *only if* free-generation quality passes a clear manual rubric; the older Bridge was trained on a different base and is not interchangeable.
