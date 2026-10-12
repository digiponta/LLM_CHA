# LLM_CHA v0.2.34.4 — GPU Context Recovery Acceptance

Status: **experimental / pending user GPU execution**, branch `v0.2.34-longterm-context`. No release tag or production truth state is modified.

## Acceptance workflow

Run three **independent `chat.py` processes** against a temporary **copy** of the real subject-keyed corpus, with an isolated checkpoint and an isolated proposition overlay.

1. Present first and second propositions for 宇宙, execute `/context-save`, check that the saved checkpoint records both IDs.
2. Start a new process, execute `/context-load` and `もう少し詳しく`, require exactly two restored IDs and the third proposition ID in the response, without re-presenting the first two IDs.
3. Write a **synthetic, isolated OUTDATED review** for both saved IDs, start another new process, load again, require `retained=0, rejected=2`, no resolvable active topic and no proposition output.

Also check subprocess exit status and unchanged original/source corpus bytes. The harness does **not** guarantee that every other chat startup artifact is isolated. The simulated review states are for filtering logic only; they do not establish scientific correctness.

## Run on RTX 3070 Ti

```powershell
git switch v0.2.34-longterm-context
git pull --ff-only origin v0.2.34-longterm-context
python -m unittest -v test_longterm_context_v02340.py test_context_restore_validation_v023341.py test_corpus_restore_adapter_v023342.py test_context_recovery_v023343.py test_context_recovery_integration_v023343.py test_context_recovery_gpu_accept_v023344.py
python context_recovery_gpu_accept_v023344.py --timeout 240
```

Target: **43/43 component tests** (40 existing + 3 new); **14/14 subprocess acceptance checks**. GPU tests launch three sequential child processes and may take several minutes. Console shows summary; detailed subprocess transcripts are in `results/context_recovery_gpu_accept_v023344.json`.

The harness is deliberately fail-closed. If a checkpoint isn't produced, report inspection should identify the first failure; a missing checkpoint might also terminate a subsequent subprocess with an error. Do not claim passing GPU acceptance until the user's results have been reviewed.
