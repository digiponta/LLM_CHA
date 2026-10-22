# LLM_CHA v0.7.3 — Trusted / Experimental Adapter Separation

Frozen shared Base LLM plus two distinct residual bottleneck adapters:
- `trusted`: remains unchanged during candidate experiments.
- `experimental`: updated using only PENDING Candidate Memory records.

This uses a residual low-rank bottleneck applied to the model's final hidden
states; it is **not attention-layer LoRA**. The output is an adapter-only
checkpoint containing an explicit `experimental` route, base-model hash,
candidate identifiers, provenance and loss history. It cannot be loaded as a
normal `LanguageModel` checkpoint.

## Windows

```powershell
git fetch origin
git switch --track origin/v0.7.3
python -m unittest -v test_dual_adapters_v073.py test_candidate_sandbox_v072.py
python train_experimental_adapter_v073.py `
  --base model/model-gpu-v1.6.2-online.pt `
  --candidates data/candidates_v071.jsonl `
  --approved data/approved_v071.jsonl `
  --output results/adapter_sandbox_v073/experimental-adapter.pt
```

The v0.7.2 PENDING candidate from prior testing can be reused. To rerun, use
a different `--output` path; experimental adapter checkpoints are not
silently overwritten. The default training schedule is a short 3-epoch
smoke test. Track the loss but **do not equate falling training loss with
quality or correctness**.

## Boundary and roadmap

- Full base and Trusted Adapter remain frozen; protected source files are
  hashed and checked for accidental changes.
- No automatic promotion, no approved memory writes, no production `chat.py`
  routing changes, and no `/sleep`.
- This is an experimental parameter-isolation proof, not yet a response-quality
  or forgetting-rate benchmark.
- v0.7.4: human-verified promotion protocol and adapter quality comparisons.
