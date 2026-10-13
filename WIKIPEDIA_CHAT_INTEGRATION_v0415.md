# LLM_CHA v0.4.15 — opt-in Wikipedia provenance-aware chat route

Interactive `chat.py` now recognizes **`/wiki PATH_TO_V0409_EVIDENCE_JSON`** and prints `wiki>` only for an explicit Wikipedia-article-backed, literal extractive definition. Existing normal `AI>` and `persona>` routes are unchanged.

This intentionally does **not** auto-fetch Wikipedia, infer source attribution for learned weights, or mark Wikipedia text as trusted. Wikipedia article intro evidence stays `UNVERIFIED`, `PENDING_REVIEW`, never trainable. The `/wiki` command bypasses AI generation/history/learning and never persists Semantic Memory or Truth State. Invalid/missing evidence is blocked; absent definitions return NO_EXTRACTIVE_DEFINITION.

## PowerShell

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_wikipedia_chat_route_v0415.py test_wikipedia_answer_prefix_v04141.py
python verify_integration_v0366.py --gpu --legacy --timeout 240
python chat.py
```

Within chat:

```text
You> /wiki results/wikipedia_article_evidence_v0409_novel.json
wiki> 【Wikipedia参照・未検証】
...
出典: https://ja.wikipedia.org/wiki/...
```

The path above must already exist from the earlier v0.4.9 inspection. The selected evidence file must pass v0.4.9 schema, digest, origin and safety checks. No separate source can be relabeled with `wiki>`.

**Scope:** explicit Wikipedia evidence display within `chat.py`. The user's broader aspiration of labeling Wikipedia-learned answers cannot be inferred from model weights; a future training provenance system would be needed for actual learned-knowledge attribution.
