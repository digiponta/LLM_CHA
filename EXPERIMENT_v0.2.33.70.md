# LLM_CHA v0.2.33.70 — Context-Aware Opinion Repair and Holdout

Motivation: The *provisional* 8-mention review measured baseline micro-F1 8/9 = 88.89%, v68 7/9 = 77.78%. v68 correctly avoided treating technical `可能性` alone as HYPOTHESIS, but missed OPINION in `量子力学的に考えると`. That review was used to select this rule; it **cannot validate** v70 generalization.

The experimental `classify_v70` restores OPINION for explicit `考えると` and selected `現象論的な見方` patterns; it deliberately does not automatically treat `量子力学的には` as OPINION. The eight **separately authored** holdout sentences are distinct from the Nagato corpus samples. They are not yet independently *adjudicated*. `proposed_gold_labels` are reference suggestions for review only, `gold_labels` start `null`, and no metrics are emitted until humans label them. Because some holdout prompts were authored after inspecting the model's weaknesses, this is a development holdout, not a final independent benchmark.

## Windows commands

```powershell
git fetch origin
git switch v0.2.33.70
git pull origin v0.2.33.70
python -m py_compile epistemic_holdout_v023370.py
python -m unittest -v test_epistemic_holdout_v023370.py test_epistemic_review_analysis_v023369.py
python epistemic_holdout_v023370.py
Copy-Item results/epistemic_holdout_v023370.json results/epistemic_holdout_review_v023370.json
```

Review the copy *independently*, editing only `gold_labels` and `review_status`, using each `context`. The `proposed_gold_labels` field represents non-authoritative illustrative guesses, not verified truth.

```powershell
python epistemic_holdout_v023370.py --score results/epistemic_holdout_review_v023370.json
```

No runtime chat behavior, candidate stores, Semantic Memory, Truth State, or LLM weights are modified. Require independently reviewed gold labels and a subsequent unseen, prospectively fixed benchmark before promoting v70.
