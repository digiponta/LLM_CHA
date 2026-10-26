# LLM_CHA v0.11.9 — chat.py experimental integration

The existing chat.py generation route can optionally consult an existing reviewed prefer_b preference **before** generation, and offer review when an accepted generated answer differs from the corpus memory candidate.

Activate in Windows PowerShell:

```powershell
$env:LLM_CHA_RECONCILIATION = '1'
python chat.py
```

Disable:

```powershell
$env:LLM_CHA_RECONCILIATION = '0'
python chat.py
```

Optional storage path: `LLM_CHA_RECONCILIATION_ROOT` (default: `data/semantic_dialogue_v0113`).

Only the existing **model generation** dispatch branch is integrated. Existing retrieval-first, Topic Context, approved-knowledge, identity and other early-return routes remain unchanged. The guard excludes force-internalized verification and FALSE/OUTDATED/CONTESTED truth states. Results stay `NOT_APPROVED` and `UNVERIFIED`, with no corpus mutation or training. Existing `chat.py` unknown rejection runs before post-generation reconciliation. No external semantic equivalence inference is claimed.

Tests:

```powershell
python -m unittest -v test_chat_semantic_reconciliation_v0119.py
python -m py_compile chat.py chat_semantic_reconciliation_v0119.py
```

User preference may be subject to current version's rigid question/context/memory fingerprint; a different phrase requires review. This is not yet integrated into GUI entrypoints or the direct retrieval path.
