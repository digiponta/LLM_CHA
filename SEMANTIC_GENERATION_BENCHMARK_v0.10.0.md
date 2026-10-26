# v0.10.0 Model-only generation benchmark

New `evaluate_semantic_generation_v0100.py` evaluates greedy free generation from original direct questions using baseline and online checkpoints without invoking `chat.py`, retrieval, Wikipedia, Semantic Memory lookup during inference, or training. It records outputs and strict normalized exact match, plus a weaker reference-contained indicator.

These questions are associated with training data, so this is NOT an independent holdout. `--holdout path.json` optionally loads a separate JSON array with `concept`, `question`, `answer`; even supplied sets are labeled unverified independence until separately audited. Do not interpret exact match as fully validated semantic accuracy.

Windows commands:

```powershell
python -m unittest -v test_evaluate_semantic_generation_v0100.py
python evaluate_semantic_generation_v0100.py --tokenizer C:/Users/inoma/git/misc/LLM_GPU/model/tokenizer-v0.7-bpe.json
```

Outputs `results/semantic_generation_v0100.json`. Greedy output is deterministic at temperature zero, but GPU-level variations may occur. Run against both checkpoints and examine per-record answers before drawing quality conclusions.
