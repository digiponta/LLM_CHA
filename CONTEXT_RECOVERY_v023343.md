# LLM_CHA v0.2.34.3 — Chat Runtime Context Recovery

Experimental branch `v0.2.34-longterm-context`. Adds **explicit, opt-in** `/context-save` and `/context-load` commands to `chat.py`, using the new `context_recovery_v023343.py` controller and the v0.2.34.2 read-only real-corpus adapter.

## Enable

```powershell
$env:LLM_CHA_MULTITOPIC="1"
$env:LLM_CHA_CONTEXT_RECOVERY="1"
$env:LLM_CHA_CONTEXT_PATH="results/context-v023343.json"
python chat.py
```

In chat: first ground a topic and request `もう少し詳しく`, then `/context-save`. Restart the same runtime and issue `/context-load`. `/reset` clears in-memory context and cursor; it does **not** delete an explicitly saved checkpoint file.

Saving persists only topic labels and IDs of previously presented propositions, not raw chat, truth decisions or model parameters. The save destination parent directory must already exist. The checkpoint is NOT automatically restored at startup.

Load validates JSON before mutating live session; re-queries the current corpus, Truth Store and proposition overlay. Saved IDs without a currently authorized match are discarded. TRUE/UNVERIFIED must remain subject to the current Truth Gate; rendering warnings remains the normal retrieval layer responsibility. No automatic training or scientific truth verification.

Note: topic names/IDs in saved files can be sensitive metadata; choose a private directory and protect the file. The path is fixed by an environment variable, never accepted from freeform user input. `chat.py` remains unchanged in behavior unless both opt-in switches are set.

## Regression (pending on Windows)

```powershell
git pull --ff-only origin v0.2.34-longterm-context
python -m unittest -v test_longterm_context_v02340.py test_context_restore_validation_v023341.py test_corpus_restore_adapter_v023342.py test_context_recovery_v023343.py test_context_recovery_integration_v023343.py
```

Expected **40 tests**: 29 existing + 5 new functional + 6 integration.

This does not yet establish real GPU behavior or all legacy compatibility. Next gate: GPU subprocess with temporary corpus and checkpoint plus full v0.2.33.82 regression.
