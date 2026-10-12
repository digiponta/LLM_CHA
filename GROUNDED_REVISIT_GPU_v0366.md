# LLM_CHA v0.3.6.6 — Grounded Revisit GPU and Unified Integration Gate

Branch: `v0.3.0` (experimental). `main` and stable `v0.2.34` are unchanged.

## Dedicated GPU acceptance

`grounded_revisit_gpu_v0366.py` invokes an isolated `chat.py` subprocess with Active retention enabled, Shadow and Context Recovery disabled, and NO explicit pins. It uses a temporary copy of the Corpus and an empty temporary Truth Overlay, and verifies:

- Explicit `宇宙について` goes through Corpus-backed retrieval with a proposition ID and no free-generated tokens.
- `もう少し詳しく` advances to the next proposition ID.
- Ten other topic queries cause topic eviction (capacity 8); `宇宙` must no longer be retained.
- Repeating `宇宙について` must re-admit the topic and show the FIRST proposition ID, rather than reuse the stale cursor.
- The re-admitted response stays grounded with Truth State diagnostics and zero generated tokens; Corpus bytes do not change.

Note: this is a **strict experimental acceptance target**, not a claim that it has already passed. If it fails, inspect `results/grounded_revisit_gpu_v0366.json` (includes the complete transcript). It does not assert factual truth of source Corpus content and does not enable Active + Context Recovery.

## 264-unit unified gate

`verify_integration_v0366.py` runs **264 distinct tests**: existing 233 + 12 Active context + 9 GPU-harness parser + 10 Grounded Revisit. It fails on skipped cases, failures, errors, or test-count changes. Optional GPU and legacy flags also invoke the existing Recovery, Shadow and Active checks, the new Grounded Revisit GPU harness, and LLM_TRY legacy regression.

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git switch v0.3.0
git pull --ff-only origin v0.3.0

python grounded_revisit_gpu_v0366.py --timeout 240
python verify_integration_v0366.py --gpu --legacy --timeout 240
```

Expected final status only after successful Windows GPU execution:

```text
INTEGRATION_GATE_V0366_PASS
```

If any GPU assertion fails, retain the failure and resolve the underlying routing/cursor behavior; do not relax validation solely to obtain a green result.
