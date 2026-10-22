# LLM_CHA v0.7.2 — Candidate-only Sandbox Learning

This experiment trains **only PENDING** records from the v0.7.1
Candidate Semantic Memory. The original model is read-only; checkpoints,
learning state and audit reports are written in a sandbox-specific directory.
No approved knowledge is promoted, and no trusted adapter or production
Semantic Memory is changed.

The existing trainer expects trusted-source labels. The wrapper temporarily
maps pending candidate pairs to `chat-manual` *inside a disposable sandbox
training JSONL only*. This is a training compatibility adapter, **not an
approval or factual-truth transition**. Its output must never be auto-deployed.

## Run on Windows

```powershell
git fetch origin
git switch --track origin/v0.7.2
python -m unittest -v test_candidate_sandbox_v072.py test_dual_semantic_memory_v071.py
```

Create a local candidate in a separate experiment store:

```powershell
python -c "from dual_semantic_memory_v071 import DualMemory; m=DualMemory('data/approved_v071.jsonl','data/candidates_v071.jsonl'); print(m.propose('v072実験の合言葉は何ですか','候補の実験回答です。','sandbox-manual:v072'))"
```

Then train:

```powershell
python candidate_sandbox_train_v072.py `
  --approved data/approved_v071.jsonl `
  --candidates data/candidates_v071.jsonl `
  --base model/model-gpu-v1.6.2-online.pt `
  --output-dir results/candidate_sandbox_v072
```

Outputs:
- `results/candidate_sandbox_v072/candidate-sandbox-v072.pt`
- `results/candidate_sandbox_v072/candidate-sandbox-state-v072.json`
- `results/candidate_sandbox_v072/candidate-sandbox-report-v072.json`

A fresh output directory is required per run to avoid overwriting or
silently reusing earlier experimental checkpoints.

## Next steps / limitations

- This is isolated full fine-tuning, **not yet LoRA/adapter-only**.
- Candidate-specific fine-tuning can degrade language quality; evaluate
  retention and new knowledge before considering any promotion.
- Rejected and approved entries are excluded from experimental data.
- The trainer can still inherit historical checkpoint fingerprint metadata
  from its baseline. This does not grant candidate approval.
- Model safety and integrity require a trusted local trainer executable.
- For safety, experiment stores should not be synced to a production runtime.
