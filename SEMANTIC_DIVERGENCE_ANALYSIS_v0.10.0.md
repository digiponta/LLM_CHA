# v0.10.0 Semantic Generation Divergence Analysis

Analyzes why direct model-only free generation produced just 6/56 exact answers despite strong teacher-forced NLL improvement. Uses existing generation report's original prompts and reference text and reruns greedy forward generation.

For each of the 56 questions, outputs first token divergence, matching-prefix length, reference-token rank at divergence and token probability for both baseline and online checkpoints.

No retrieval, Semantic Memory lookup during generation, training or /sleep. Direct questions are training-associated, **not independent holdout**. Rank and probability are diagnostics of the first divergence, not semantic correctness.

Windows:
```powershell
git pull --ff-only
python -m unittest -v test_analyze_semantic_divergence_v0100.py
python analyze_semantic_divergence_v0100.py --tokenizer C:/Users/inoma/git/misc/LLM_GPU/model/tokenizer-v0.7-bpe.json
```

Report: `results/semantic_divergence_v0100.json`.
No Windows verification has been run yet.
