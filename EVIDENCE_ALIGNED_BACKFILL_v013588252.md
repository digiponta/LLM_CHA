# v0.13.58.82.52 — Aligned negative backfill from rejection cache

Fixed `NO_ALIGNED_NEGATIVES` when the GUI reuses an existing rejected response rather than generating it again. The GUI now records an Evidence-Aligned negative example from the **cached discarded candidate plus current matching evidence**, without calling the LLM again. The aligned capture is deduplicated, and no model training is automatically started.

Windows:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.52-aligned-backfill
python chat_gui.py
```

Ask `宇宙とは`, then `もっと詳しく`. In Diagnostics expect `[Evidence-Aligned Negative Backfill] RECORDED` (or `DUPLICATE`). Close GUI and run:
```powershell
python train_evidence_aligned_negative_v013588251.py `
  --negative-data data/negative_evidence_aligned_v013588251.jsonl `
  --base-model model/model-gpu-v1.6.2-online.pt `
  --tokenizer C:\Users\inoma\git\misc\LLM_GPU\model\tokenizer-v0.7-bpe.json
Get-Content results/evidence_aligned_negative_v013588251.json -Encoding UTF8
```

Note: The cache keys by evidence excerpt and model revision. Backfilling only occurs when the precise cache lookup succeeds; no historical negative is converted if its evidence or model revision cannot be matched. Source trust remains EXTERNAL_UNVERIFIED. No /good, positive learning, automatic weight updates or production checkpoint promotion.
