# v0.13.58.82.53 Prefix-Weighted Negative Learning

Adds `train_prefix_negative_v013588253.py`, an independent negative-only experiment. It uses the same saved Evidence-conditioned prompt and rejected completion as v0.13.58.82.51, but optionally increases negative loss weight over the first N rejected-answer tokens. It retains frozen-baseline KL regularization, conservative gradient clipping, per-case NLL gate, and separate candidate checkpoint output. No /good, automatic positive learning, or production promotion.

The parameters `--prefix-tokens 0 --prefix-weight 1` reproduce uniform negative weights. The experimental focused setting is `--prefix-tokens 8 --prefix-weight 4`. Both must start from the *same original* base model, with separate outputs and reports. Prefix weighting is on the rejected answer targets only, not prompt targets. This is intended to change early selection, but **is not a guarantee**; it can shift the model to a different invalid sentence. The only implemented acceptance screen is NLL: independently compare generations and Evidence Gate before any production use.

## PowerShell

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.53-prefix-negative
python -m unittest -v test_prefix_negative_v013588253.py test_evidence_aligned_negative_v013588251.py
python train_prefix_negative_v013588253.py `
  --negative-data data/negative_evidence_aligned_v013588251.jsonl `
  --base-model model/model-gpu-v1.6.2-online.pt `
  --tokenizer C:\Users\inoma\git\misc\LLM_GPU\model\tokenizer-v0.7-bpe.json `
  --steps 3 --prefix-tokens 8 --prefix-weight 4 `
  --output results/prefix_negative_v013588253.candidate.pt `
  --report results/prefix_negative_v013588253.json
Get-Content results/prefix_negative_v013588253.json -Encoding UTF8
```

If `CANDIDATE_ONLY` is reported, compare the candidate with the original model under the saved Evidence snapshot:

```powershell
python compare_evidence_replay_v013588249.py `
  --base model/model-gpu-v1.6.2-online.pt `
  --candidate results/prefix_negative_v013588253.candidate.pt `
  --tokenizer C:\Users\inoma\git\misc\LLM_GPU\model\tokenizer-v0.7-bpe.json `
  --negative-data data/negative_teacher_signals_v013588244.jsonl `
  --evidence-json results/evidence_snapshot_v013588249.json `
  --output results/prefix_generation_compare_v013588253.json
Get-Content results/prefix_generation_compare_v013588253.json -Encoding UTF8
```

Compare the new report with `results/evidence_aligned_generation_comparison.json` (uniform-weight baseline). Note the first token probability and evidence gate; no candidate is automatically promoted. These scripts have not been run on the user's local RTX 3070 Ti.
