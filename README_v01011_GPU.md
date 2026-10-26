# v0.10.1.1 — GPU Decoding Benchmark

These files only implement the real-checkpoint loading adapter. They do not change `chat.py` or perform online learning.

## Windows PowerShell

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.10.1-semantic-decoding
git pull --ff-only

python -m unittest -v test_decoding_v0101.py test_decoder_factory_v01011.py

# IMPORTANT: replace with the EXACT online/base checkpoint used in v0.10.0.
$env:LLM_CHA_DECODE_MODEL = "C:\Users\inoma\git\misc\LLM_CHA\model\YOUR_V0100_CHECKPOINT.pt"
$env:LLM_CHA_DECODE_TOKENIZER = "C:\Users\inoma\git\misc\LLM_GPU\model\tokenizer-v0.7-bpe.json"

# The input is a JSON array of objects with id, prompt, reference, and optional split.
python evaluate_decoding_v0101.py --factory decoder_factory_v0101:load --cases data/decoding_dev_v0101.json --output results/decoding_comparison_v0101.json
```

Input illustration (not an actual evaluation case):
```json
[{"id":"sample","prompt":"人: 質問\\nAI: ","reference":"正解","split":"dev"}]
```

Use the same prompt building and 56 reference responses as the earlier divergence analysis; this repo may not include the 56-case data from the local v0.10.0 study. Do not evaluate on synthetic examples and claim 56-case results.

A genuine comparison needs separate base vs online runs, an independent paraphrase split, and manual or separately calibrated semantic/grounding evaluation. Existing experiment runner measures exact match, token prefix and latency only.

The factory fails closed if no explicit model checkpoint is provided. It checks tokenizer vocabulary size and disables gradient updates. A CPU fallback is allowed for diagnostics.
