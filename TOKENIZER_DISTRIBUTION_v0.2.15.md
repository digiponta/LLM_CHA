# LLM_CHA v0.2.15 — Tokenizer and Response Distribution Diagnosis

No model weights or data are changed. These are observational diagnostics, intended to explain why generated responses favor generic fillers.

## Local execution

```powershell
git fetch origin
git switch --track origin/v0.2.15
python -m unittest -v test_tokenizer_distribution_v0215.py test_diagnostics_v0214.py
python diagnose_tokenizer_distribution_v0215.py
python diagnose_generic_amplification_v0215.py
```

To recalculate the generation samples from the same test slice before generic amplification analysis:
```powershell
python generation_quality_v0214.py --max-rows 30
```

Reports:
- `results/tokenizer_distribution_v0215.json`: each dataset's generic-response fraction, common answers, unique response ratio, short answer rate, BPE tokens per character, unknown-token fraction.
- `results/generic_amplification_v0215.json`: exact matched 30-prompt reference-vs-generated generic fraction and fragmentation. Uses v0.2.14 saved generation results. Both use the same question subset.

## Interpretation

- Generic replies frequent in training: investigate target-response filtering, weighting and data distribution before more SFT.
- Generic replies rare in reference samples but frequent in raw generation: generation collapse, limited language modeling, autoregressive feedback, or decoding bias likely contributes. Do NOT assert sole causation from this association.
- Unusually high tokens/character: tokenizer fragmentation may undermine effective context capacity. `<UNK>` rare in byte-level BPE does not mean segmentation is efficient.
- Response type and topic, duration, and source speaker matter. Simple exact-string dictionaries undercount paraphrased generic answers.
- The v0.2.11 dataset repeats synthetic dialogue sessions, so raw sample counts do not mean unique topic diversity.
- This diagnostic is not a definitive attribution of causes. Further work would involve matched data interventions and controlled retraining.

Existing raw generation script may emit a Python deprecation warning due to positional maxsplit; this warning does not invalidate its results.
