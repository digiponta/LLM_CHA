# LLM_CHA v0.3.6.4 — Three-Mode GPU Active Retention Acceptance

Development branch `v0.3.0` only. Stable `main` / `v0.2.34` unchanged.

Runs three independent `chat.py` subprocesses for OFF, SHADOW and ACTIVE. Explicitly fixes feature flags in each subprocess to prevent inherited PowerShell flags from contaminating evaluation. Copies the corpus and uses an isolated blank proposition overlay.

### Acceptance coverage
- 10 explicitly named topics exceed the normal 8-slot cache.
- Active mode pins `宇宙` and `GPU` and must evict at least one non-pinned topic.
- `宇宙の話に戻って` must resolve the protected topic.
- `/reset` clears active topics; unresolved anaphora must fail closed.
- Compare identical Truth Gate / response and retrieval signatures for first-turn `宇宙とは`, `GPUとは`, `CPUとは` across OFF, SHADOW and ACTIVE.
- Check corpus bytes remain unchanged and all three processes exit normally.
- Reports diagnostics and full transcripts to `results/active_retention_gpu_accept_v0364.json`.

This test does not prove correctness for all topics, full v0.3.5 auto-pin behavior, or Context Recovery + Active coexistence. No production learning or memory storage is intended.

### Commands

```powershell
git switch v0.3.0
git pull --ff-only origin v0.3.0
python -m unittest -v test_active_topic_context_v0363.py test_active_retention_gpu_accept_v0364.py
python active_retention_gpu_accept_v0364.py --timeout 240
python verify_integration_v0362.py --gpu --legacy --timeout 240
```

Expected 20 new Active test cases (12+8), in addition to existing 233 integration cases. Report `pass: true` is an acceptance *target* until actual Windows GPU execution.

### Next
Assess topic eviction/cursor synchronization and ungrounded generative responses after topic churn. Keep Active Recovery disabled until a separate validated restore bridge exists.
