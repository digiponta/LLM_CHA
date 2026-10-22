# LLM_CHA v0.6.11 — Full Wagahai Training

The v0.6.4 ingestion provides **426 chunks** of *吾輩は猫である* (work 789).
v0.6.7 trained only a random sample of its windows in each 160-step epoch.
This version traverses **every token window of the ingested novel each
epoch**, while interleaving Persona Replay batches to reduce forgetting.

## PowerShell (local GPU required)

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch --track origin/v0.6.11
python train_wagahai_full_v0611.py --dry-run
python train_wagahai_full_v0611.py --epochs 2 --persona-ratio 0.5
Get-Content results/wagahai_full_v0611.json -Encoding utf8
```

Defaults: original v94 checkpoint, existing `data/nagato_chat.jsonl`
persona data, 50% persona optimizer steps, block size 128, 2 epochs,
held-out work 1567 `走れメロス`. No existing checkpoint overwrite.
Expected work counts: 789=426, 1567=14; mismatches abort rather than
silently learning an incomplete/changed dataset. This confirms processed
**corpus** coverage, not byte-for-byte verification against Aozora source.
The 128-token windows of the concatenated token stream are each visited
once per epoch; the final partial batch is included. Report includes
literature_coverage=1.0.

This performs **continued next-token pretraining**, not exact memorization
and not automatic Semantic Memory registration. Evaluate independent
literature NLL, held-out persona NLL, identity and actual chat.py quality
before selecting the output for GUI use. Do not promote an experimental
model to stable solely on the basis of the training loop completing.

The default output is `model/model-llm-cha-wagahai-full-v0611.pt`
with report `results/wagahai_full_v0611.json`. Use unique
`--output` and `--report` paths for reruns.
