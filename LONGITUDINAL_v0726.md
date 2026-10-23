# LLM_CHA v0.7.26 — Experimental Longitudinal Learning and Forgetting

Adds a separate **read-only** benchmark. Fixed training and held-out
paraphrase prompts are evaluated against the same Base LLM with different
time-ordered Experimental Adapter checkpoints. Exact-match accuracy
is reported separately for training vs paraphrase probes.

The old checkpoint must be FIRST and the new checkpoint LAST. Forgetting
is the proportion of initially correct questions that are no longer
correct in the final checkpoint. One checkpoint is insufficient to
measure forgetting and reports `null`.

No Candidate promotion, automatic training, or Trusted checkpoint changes.
Synthetic v072 paraphrases come from the existing v0.7.8 manual
definitions. For other Candidates, only training probes are prepared:
author independent paraphrases before claiming generalization.

## PowerShell

```powershell
git fetch origin
git switch --track origin/v0.7.26
python -m unittest -v test_longitudinal_v0726.py
python prepare_longitudinal_probes_v0726.py
python benchmark_longitudinal_v0726.py `
  --checkpoints results/experimental_sleep_v0722/experimental-sleep-88c3cbc845c6ff0d0973.pt `
  --probes results/experimental_longitudinal_v0726/probes.json
```

That single-checkpoint command supplies an initial reproducibility
baseline and will report forgetting as **not measurable**. Once you
have recorded an additional checkpoint after adding a Candidate and
running `/sleep`, rerun with both checkpoint paths in chronological
order. The evaluation uses raw Experimental generation, not direct
Candidate Evidence answer.

Interpretation: answers are compared to their unverified stored
reference strings, not to independent factual truth. For an actual
cross-checkpoint forgetting study, maintain an unchanged set of old
knowledge probes as well as new probes; group-level results reveal
whether a new training round hurt old knowledge.
