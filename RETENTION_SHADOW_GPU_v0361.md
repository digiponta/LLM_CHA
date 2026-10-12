# LLM_CHA v0.3.6.1 — Shadow ON/OFF GPU Equivalence Gate

Development branch: `v0.3.0`. Stable `v0.2.34` and `main` unchanged.

## Objective
Demonstrate that read-only Adaptive Retention Shadow does not change user responses, Truth Gate outputs or Context Recovery behavior. Two independent modes (forced OFF and ON) are run in six `chat.py` subprocesses, with separate copies of an existing Corpus, proposition Truth Overlay and checkpoint. No production stores are changed by the harness.

Both modes execute:
1. `宇宙について教えて`, `もう少し詳しく`, `/context-save`, `/retention-stats`.
2. Fresh process: `/context-load`, `もう少し詳しく`, `/retention-stats`.
3. Synthetic OUTDATED status applied to the two saved proposition IDs; fresh process: `/context-load`, `もう少し詳しく`, `/retention-stats`.

Normalized signatures compare `AI>`, proposition IDs and truth states, retrieval/grounded outputs, Truth Gate and context save/load outcomes. Startup banners and shadow-only stats are excluded; separately assert ON stats are present and OFF stats are disabled. Each process must return 0; checkpoints must exist and Corpus copies must remain untouched.

## Commands
```powershell
git switch v0.3.0
git pull --ff-only origin v0.3.0
python -m unittest -v test_retention_shadow_gpu_accept_v0361.py
python retention_shadow_gpu_accept_v0361.py --timeout 240
```

Expected 6 new unittest cases, for **92 total** in the v0.3.0 retention suite (86 previous + 6 new), pending local validation. The GPU harness prints `"pass": true` when all checks pass, and exits nonzero on mismatch. Report: `results/retention_shadow_gpu_accept_v0361.json`.

## Limitations
No guarantee of deterministic sampling for all future model configurations; this fixture uses retrieval-dominant topics. Synthetic OUTDATED labels test the gate path, not scientific truth. This harness does not isolate every legacy runtime file nor establish automatic topic importance inference. It does not enable policy-controlled eviction. Further realistic interaction and full v0.2.34 regression are required before a new stable release.
