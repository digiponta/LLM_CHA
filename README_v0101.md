# LLM_CHA v0.10.1 — Frozen Decoder Comparison

Experimental add-on. Does not change production chat, checkpoints, online learning, or model weights.

## Test
```powershell
python -m unittest -v test_decoding_v0101.py
```

## Connect to real model

Create decoder_factory_v0101.py defining `load()` which returns the existing initialized, frozen `(model, tokenizer)` pair. Use the SAME weights, prompt format, checkpoint and tokenizer as the v0.10.0 baseline. The factory must not train the model.

Input JSON: `[{"id":"001","prompt":"人: 質問\nAI: ","reference":"正解","split":"dev"}]`

```powershell
python evaluate_decoding_v0101.py `
  --factory decoder_factory_v0101:load `
  --cases data/decoding_dev_v0101.json `
  --output results/decoding_comparison_v0101.json
```

The runner writes JSON and CSV. It compares greedy, beam width 3 and 5, repetition penalties, length penalties and generation lengths. It reports exact match, matched token prefix, generated length and latency.

## Evaluation integrity

- Reference text is passed to scoring ONLY, not to decode.
- Hyperparameters should be selected using the development set ONLY.
- Independent paraphrases and unknown cases should be held out until final evaluation.
- Semantic accuracy, evidence faithfulness and unknown rejection are NOT scored by this prototype; those require independent assessment.
- EOS and newline stop generation, mirroring the legacy chat.py path.
- Beam decoding is sequential and not latency-optimized.
- For exact historical comparison, harmonize max tokens, prompts, checkpoint and stop conditions.
