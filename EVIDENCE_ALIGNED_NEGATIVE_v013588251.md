# LLM_CHA v0.13.58.82.51 — Evidence-aligned negative learning

The GUI now records each newly rejected Evidence Gate generation in `data/negative_evidence_aligned_v013588251.jsonl`, including the **exact prompt** constructed by `generation_prompt(topic, excerpt[:450])`, the discarded LLM reply, the gate, and a source URL. No /good, positive-teacher supervision, or auto-training is reintroduced.

A new isolated script `train_evidence_aligned_negative_v013588251.py` evaluates token probabilities using the original prompt followed by rejected answer (answer-token positions only), and trains with a bounded unlikelihood term plus KL to a frozen baseline checkpoint. It saves an experimental candidate **only** if every recorded negative becomes less likely with NLL increase below the configured maximum. Production is never changed. The original v0.13.58.82.47 trainer remains available for comparison.

## Windows

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.51-evidence-aligned-negative
python -m unittest -v test_evidence_aligned_negative_v013588251.py
python chat_gui.py
```

Ask `宇宙とは`, then `もっと詳しく`. Look for `[Evidence-Aligned Negative] RECORDED` in Diagnostics. Previously rejected candidates that are served from the inference cache are **not newly generated** and therefore cannot create a new aligned training record; use a changed evidence/checkpoint or clear the experimental rejection cache file if intentionally sampling anew. Do not delete the separate negative signal archive.

Then stop the GUI and run:

```powershell
python train_evidence_aligned_negative_v013588251.py `
  --negative-data data/negative_evidence_aligned_v013588251.jsonl `
  --base-model model/model-gpu-v1.6.2-online.pt `
  --tokenizer C:\Users\inoma\git\misc\LLM_GPU\model\tokenizer-v0.7-bpe.json
Get-Content results/evidence_aligned_negative_v013588251.json -Encoding UTF8
```

This script may be computationally slower because it evaluates each answer-token position separately. On the initial single record, 3 steps is the default. The training objective does **not** guarantee that generated text changes or that the Evidence Gate will accept the candidate. The next benchmark should replay with `compare_evidence_replay_v013588249.py --candidate results/evidence_aligned_negative_v013588251.candidate.pt --evidence-json results/evidence_snapshot_v013588249.json`, but only if a candidate checkpoint was actually saved.

Caution: the rejection gate is a conservative substring-matching filter, not a comprehensive truth detector. Negative signals should be treated as evidence-gate violations rather than universal factual falsehoods.
