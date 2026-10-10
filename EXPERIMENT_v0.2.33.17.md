# LLM_CHA v0.2.33.17 — Out-of-Distribution Copy Robustness

The v0.2.33.16 restricted combinatorial grammar achieved 40/40 training probes, 80/80 validation, and 80/80 test exact copy. This **does not establish arbitrary Japanese copying**. This branch probes out-of-distribution limits with the v0.2.33.16 checkpoint **frozen** and unchanged.

## Evaluation groups

- **In-grammar control:** 20 held-out validation examples from the previous deterministic 480/80/80 split (seed 42)
- **Unseen vocabulary:** 8 examples using new colors, objects, actions and locations
- **Unseen syntax:** 8 examples with questions, subordinate clauses, rearranged argument order, etc.
- **Longer sentences:** 4 longer strings built from several previous-template-like sentences
- **Multiple sentences:** 4 general two- or three-sentence samples
- **Symbols and numbers:** 8 instances involving URLs, numeric literals, punctuation, and JSON
- **Original benchmark:** all 8 held-out probes from v0.2.33.9

The categories are diagnostic stressors, not cleanly orthogonal linguistic partitions. The previous benchmark has been seen in development conversations, so it is an informative regression set rather than a pristine final holdout.

## Metrics

Strict text match; strict generated-token match including EOS; matched initial token count; source-tokenizer roundtrip; generated output; prompt and source token counts; EOS stop; context-length skip count.

Greedy temperature=0, repetition penalty=1.0. No training, optimizer, checkpoint saving, threshold tuning or DSS/Memory/Bridge changes.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.17
git pull origin v0.2.33.17
python -m unittest -v test_copy_ood_robustness_v023317.py
python evaluate_copy_ood_robustness_v023317.py
```

JSON report: `results/copy_ood_robustness_v023317.json`.

The script refuses to overwrite the existing result file. Re-execution needs a different `--out` path.

## Decision guide

If in-grammar control works but new words fail, broaden lexical exposure while retaining validation-only selection. If syntax fails, add independent templates and test held-out template families. If only longer examples fail, examine length sensitivity and EOS. If even in-grammar control fails, verify that the v0.2.33.16 checkpoint/tokenizer are loaded and unchanged. Never claim general semantic understanding based on copy accuracy.
