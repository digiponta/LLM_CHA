# LLM_CHA v0.2.13 — Fixed-Test Japanese LM and Context Ablation

The goal is *diagnosis before increasing data*, not further tuning. No model weights are modified.

## Implemented

`diagnose_models_v0213.py` loads the three existing checkpoints and scores the **same held-out RealPersonaChat test split**. It computes token-weighted assistant answer NLL under teacher forcing in two conditions:
- **With context:** full preformatted `人:/AI:` dialogue prompt.
- **Without context:** final `人:` utterance only.

Metrics: NLL (lower is better), perplexity, positive `context_gain = no_context_NLL - with_context_NLL`, and per-example fraction helped by context.

The comparison measures the likelihood of *reference assistant replies*. It **does not measure generated grammatical correctness, factual correctness, response diversity, or conversational relevance directly**. The same test data and tokenizer are necessary for all checkpoints; training/checkpoint losses are not comparable across differing corpora. If test examples leak into training, discard the conclusions.

## Execute locally

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch --track origin/v0.2.13

python -m unittest -v test_diagnose_models_v0213.py test_generalization_v0212.py

python diagnose_models_v0213.py --dataset data/dialogue_generalization_v0212/test.jsonl --max-rows 200
```

Results written to `results/model_diagnostic_v0213.json`. Use more rows for a stronger aggregate:
```powershell
python diagnose_models_v0213.py --max-rows 1000
```

Use the *same model inference settings* when independently comparing actual generated conversations: `--temperature 0 --probe-count 3 --dialogue-history-turns 2`. For a direct causal context comparison, repeat the same checkpoint with `--dialogue-history-turns 0`. Record at least 30 unseen multi-turn questions and manually score topical relevance, grammaticality, and substantive continuation. Keep the old quality/rerank gates fixed; do not count rule-based profile or canonical retrieval answers as model outputs.

## Interpretation

- Higher context gain **and** lower NLL with context: stronger reference answer modeling using dialogue history.
- Higher context gain but poor generated conversation: decoder, insufficient generalization, and/or training distribution mismatch may remain.
- Near-zero or negative context gain: dialogue history does not help on this test sample; prioritize architecture/pretraining alignment over collecting more synthetic SFT.
- Low NLL alone is not good dialogue: bland replies may be frequent in the corpus.
- Incomplete language capacity might require expanded Japanese pretraining. Avoid claiming this until context ablation and out-of-distribution human examples are evaluated.

Runtime note: scoring with model.forward may require GPU memory; score one checkpoint at a time. The final rows in the fixed test can overlap semantically with train even with dialogue-ID split; hence this is *not* a fully independent generalization benchmark.
