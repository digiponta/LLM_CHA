# v0.4.14.1 — Wikipedia answer provenance prefix `wiki>`

A dedicated offline formatter `wikipedia_answer_prefix_v04141.py` marks answers sourced from Japanese Wikipedia with `wiki>`. It is **not** connected to the interactive `chat.py` runtime at this stage, because the v0.4.6–v0.4.14 Wikipedia pipeline only creates **UNVERIFIED and non-trainable** research candidates. It would be misleading to treat these as learned, verified or autonomous answers.

Example when the user explicitly requests display of the cited Wikipedia source:

```text
You> 小説とは
wiki> 【Wikipedia参照・未検証】
小説は文学の形式の一つである。
出典: https://ja.wikipedia.org/wiki/小説
```

Caller must pass explicit Wikipedia source type, HTTPS ja.wikipedia.org article URL, UNVERIFIED, non-trainable, and `explicit_source_request=True`. Existing `AI>` and `persona>` remain unchanged. No training, automatic routing, truth promotion, corpus edits, Semantic Memory mutation, or `/sleep` integration.

PowerShell:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_wikipedia_answer_prefix_v04141.py
```

For integration with chat runtime after Wikipedia evidence review, implement a separate explicitly opt-in route with provenance and truth policy preserved; do not automatically output or learn raw search snippets.
