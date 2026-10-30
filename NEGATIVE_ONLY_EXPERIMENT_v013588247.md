# LLM_CHA v0.13.58.82.47 — Negative-only trainer experiment

Separate experiment script `train_negative_only_v013588247.py` reads the already recorded negative teacher signals. It does not use `/good`, create positive answers, invoke the existing `/train` path, or auto-train on GUI rejection.

**How it works:** Unlikelihood penalty increases the negative response's answer-token NLL, regularized by KL divergence to a frozen copy of the input checkpoint. Defaults: 6 update steps, LR 1e-6, negative penalty 0.05, KL weight 1.0, max allowed per-record NLL increase 0.35. These are experimental, not optimal hyperparameters.

Result is saved as a **separate candidate checkpoint** in `results/`, only if average negative NLL rose within the configured per-case limit. A JSON diagnostic report always records pre/post negative NLL. Original checkpoint remains untouched.

This does **not** validate CPU/GPU knowledge retention, improve generation quality by itself, or guarantee evidence-grounded response. Do not deploy the candidate without independent holdout and response-level checks. In contrast to the v0.13.58.82.43 contrastive mechanism, no user-approved positive text is required; strong negative-only gradients can degrade language quality, which motivates low LR and KL regularization.

## Windows
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.47-negative-only-experiment
python -m unittest -v test_negative_only_experiment_v013588247.py test_rejection_reuse_v013588246.py
python train_negative_only_v013588247.py --negative-data data/negative_teacher_signals_v013588244.jsonl --base-model model/model-gpu-v1.6.2-online.pt --tokenizer C:\Users\inoma\git\misc\LLM_GPU\model\tokenizer-v0.7-bpe.json
Get-Content results/negative_only_v013588247.json
```

The GUI `/good` remains disabled; `/negstats` remains read-only. Running `/train` manually still invokes the independent legacy positive trainer, **not** this script.

Status `CANDIDATE_ONLY` means only negative-NLL screening passed; `NO_PROMOTION_DIAGNOSTIC` means no candidate was saved. Neither indicates production promotion.

Future improvement: report generation before/after, add holdout retention baselines, measure model revision, and bind negative records to the exact normalized generation prompt rather than topic-only.
