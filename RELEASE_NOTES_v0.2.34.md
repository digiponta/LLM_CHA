# LLM_CHA v0.2.34 — Stable Release

**Long-Term Context Recovery & Truth-Aware Restore**

## Features
- v0.2.34.0: bounded checkpoint for topic names and presented proposition IDs.
- v0.2.34.1: restore validation against current proposition IDs, corpus and subject Truth Gate.
- v0.2.34.2: read-only real corpus adapter.
- v0.2.34.3: opt-in `/context-save` and `/context-load` commands in `chat.py`.
- v0.2.34.4: GPU multi-process restart and synthetic OUTDATED revocation acceptance harness.
- v0.2.34.5: atomic checkpoint replacement, pre-read checkpoint size guard and multi-topic restore regressions.

## Validation (2026-10-12, user-run Windows / RTX 3070 Ti)
- Combined LLM_CHA regression suite: **141/141 PASS** (94 baseline + 47 new; one invocation, 0.340s).
- GPU recovery acceptance: **14/14 PASS**; 3/3 chat subprocesses exit 0.
- Legacy LLM_TRY v10.16.5: **48/48 historical cases PASS**, 6/6 integration checks PASS.
- Final `RELEASE_GATE_V02334_PASS`.

## Usage
```powershell
$env:LLM_CHA_MULTITOPIC="1"
$env:LLM_CHA_CONTEXT_RECOVERY="1"
$env:LLM_CHA_CONTEXT_PATH="results/context-v023343.json"
python chat.py
```
Save with `/context-save`; restore only when requested with `/context-load`. A restored proposition ID is not an authorization decision; current corpus and Truth State are rechecked.

## Reproduction
```powershell
python verify_release_candidate_v02334.py --gpu --legacy
```

## Limits and security boundaries
- GPU OUTDATED labels are synthetic testing fixtures, not external scientific validation.
- Temporary corpus/overlay/checkpoint isolation does not encompass all legacy runtime support files.
- Atomic `os.replace` does not establish crash/power-loss durability or transactions during concurrent corpus updates.
- Saved topic names/IDs are metadata and should be protected. Checkpoint recovery is opt-in.
- This document describes validated release contents. Repository merge, tag and GitHub Release must be recorded separately when performed.
