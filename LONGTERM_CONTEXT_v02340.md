# LLM_CHA v0.2.34.0 — Long-Term Context Checkpoint Prototype

Status: **Experimental**. Independently introduced on branch
`v0.2.34-longterm-context`. The stable tag `v0.2.33.82` is unchanged.

## Goal

Keep conversation-topic selection and IDs of already shown propositions
separate from Semantic Memory and model weights. Save/export an explicit,
bounded snapshot to later permit recovery across sessions.

## Prototype

`longterm_context_v02340.ContextCheckpoint` exposes:
- `remember(topic, proposition_id)`: add unique ID, activate topic
- `switch(topic)`: switch to a previously tracked topic
- `reset()`: discard transient state
- `export()` / `restore(data)`: deterministic schema-tagged JSON
- `digest()`: SHA-256 of canonical snapshot

Limits: 16 tracked topics, 512 proposition IDs total, 128-character
maximum topic and ID lengths. No automatic file I/O or persistence,
no raw conversation messages, no reviews, no Truth State writes.

**Not yet integrated with `chat.py`**. Exporting state does not grant
permission to reuse propositions after their Truth State or underlying
corpus has changed; the next stage must bind fingerprints and re-check
the authoritative Truth Gate on restoration.

## Test

```powershell
git fetch origin
git switch --track origin/v0.2.34-longterm-context
python -m unittest -v test_longterm_context_v02340.py
```

Expected: 8 prototype tests (not yet run on the user's Windows machine).
Retest old v0.2.33.82 regression suite before merging any integration.
