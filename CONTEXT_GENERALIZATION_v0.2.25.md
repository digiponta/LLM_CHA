# v0.2.25 — Context Generalization + Japanese Generation Quality

Experiment only. Uses v0.2.21 as a fixed training start, retains v0.2.24 as baseline, and trains 18 distinct topic-conditioned prompts with an explicit expansion weight of **12**, instead of the 6 × 60 pilot. Six other manually authored topics are left out. The 3,000 examples of replay come from the pre-existing v0.2.12 training split, filtered by holdout keywords. This is **not** a fully independent semantic-disjoint corpus; manually inspect contamination.

## Windows PowerShell
```powershell
git fetch origin
git switch --track origin/v0.2.25
python -m unittest -v test_context_generalization_v0225.py test_context_weighted_v0224.py
python prepare_context_generalization_v0225.py
python train_context_generalization_v0225.py --dry-run
python train_context_generalization_v0225.py
python evaluate_context_generalization_v0225.py
```

Expected context exposure per epoch: 18×12 = 216; replay ≈3,000; anchors 9×10=90; total ≈3,306 (actual counts printed). Output checkpoint: `model/model-llm-cha-context-generalization-v0225.pt`.

## Evaluation

The new evaluator scores both the 18 training topics and 6 unseen topics. It reports matched-vs-mismatched context NLL margin, diagonal-best fraction, raw Greedy responses, exact focus keyword hits and very short outputs for each checkpoint. Open `results/context_generalization_v0225.json` to **read and manually score full generated Japanese**; lexical hits and shortness alone are not valid measures of grammaticality, logic, semantic relevance or truthfulness. Re-run `diagnose_models_v0213.py` on the same 1000 external heldout examples for general LM retention. Run normal `chat.py` to confirm gate protections separately.

Caveats: synthetic data, limited 6-topic heldout, keyword-based split, no independently validated human ratings; no claim of generalization until corroborated. No remote GPU tests have run.
