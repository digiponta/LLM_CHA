# LLM_CHA v0.7.43 — Approved Semantic ID paraphrase training experiment

This version prepares multiple questions for each Approved source-evidence ID.
**Training**: the original form and two alternates. **Holdout**: two
different questions excluded from training. It provides a deterministic
model-only free generation baseline, a separate opt-in fine-tuning run,
and a post-training evaluation. It does **not** automatically change the
production Trusted model or the currently active conversation runtime.

## Windows PowerShell

```powershell
git fetch origin
git switch --track origin/v0.7.43
python -m unittest -v test_approved_paraphrase_v0743.py test_trusted_generation_v0742.py
python prepare_approved_paraphrase_v0743.py
python evaluate_approved_paraphrase_v0743.py --output results/approved_paraphrase_baseline_v0743.json
python train_approved_paraphrase_v0743.py
python evaluate_approved_paraphrase_v0743.py --model results/approved_paraphrase_v0743/experimental-trusted.pt --output results/approved_paraphrase_after_v0743.json
```

Important: the training action above is opt-in. It creates a *distinct*
checkpoint under `results/`, using `online_train.py`; the live
`model/model-gpu-v1.6.2-online.pt` and its learning state are untouched.
The training input contains ONLY train-split questions. The evaluation
script calls `LanguageModel.generate` directly (no Wikipedia or
Corpus lookup) and reports each generated answer.

Compare holdout `answer_containment` as well as the actual text in both
evaluation JSON reports. Containment is a narrow exact-substring measure,
not semantic equivalence. The dataset is currently very small (2
holdouts per Approved source ID). A holdout improvement cannot by itself
establish broad generalization. Do not deploy the experimental
checkpoint to production without independent regression testing.

Training outputs cannot be overwritten accidentally. If retrying after
a failed experiment, choose *new* --output, --state and --train-log paths.
