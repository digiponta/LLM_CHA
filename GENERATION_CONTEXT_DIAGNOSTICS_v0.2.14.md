# LLM_CHA v0.2.14 — Generation vs Context Diagnosis

This branch introduces **diagnostics only**, no weight updates.

## A: Context understanding (teacher-forced)
`context_ablation_v0214.py` scores the SAME held-out reference answer with:
1. genuine history;
2. last user utterance only;
3. shuffled history from a different held-out row.

The real-vs-shuffled delta helps distinguish *relevant context* from merely including more prior text. This is a lightweight control, NOT rigorously length-matched or guaranteed semantically unrelated. All comparisons use the same tokenizer, row set and checkpoint API.

## B: Japanese generated-answer quality (free generation)
`generation_quality_v0214.py` generates one deterministic raw response per test prompt **without** external chat gates, retrieval, reranking or character-specific rule responses. Reports generic reply fraction, exact consecutive repetition, very-short/empty fraction and distinct answer fraction. These automatic indicators do not measure grammaticality, truth or subject relevance.

A separate CSV with generated text and empty 1–5 human rating columns is written for evaluation of naturalness, topic relevance and substantive continuation. Score the same prompts and model outputs without knowing model identity where possible. Checkpoint loss/NLL alone cannot prove fluent dialogue.

## Local commands
```powershell
git fetch origin
git switch --track origin/v0.2.14
python -m unittest -v test_diagnostics_v0214.py test_diagnose_models_v0213.py
python context_ablation_v0214.py --max-rows 300
python generation_quality_v0214.py --max-rows 30
```

Outputs: `results/context_ablation_v0214.json`, `results/generation_v0214.json`, and `results/generation_v0214.manual.csv`.

## Interpretation

If genuine context does not beat shuffled history, then past turns may not be contributing topic-specific information. If genuine context helps NLL but generated replies remain generic or malformed, prioritize language modeling/data quality and decoder experiments over more task-specific SFT. Check whether all three models were scored on the same token sample. Sample sizes and uncertainty intervals matter.

Limitations: training split generation is inherited from v0.2.4 and may not eliminate all semantic overlap; the shuffle test may introduce distribution shift; generation heuristic metrics are imperfect; manual review remains necessary. No GPU or Python runtime results have yet been verified for this branch.
