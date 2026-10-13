# LLM_CHA v0.4.16 — Automatic UNKNOWN → Wikipedia fallback

When ordinary chat semantic dispatch reaches `BLOCK/UNKNOWN` for a **definition-style question** (e.g. `小説とは` or `哲学について教えて`), the runtime now makes a **read-only, exact-title** lookup against Japanese Wikipedia via the existing v0.4.9 MediaWiki article evidence client, and applies the frozen v0.4.12 extractive alignment. On matching source/title and literal source evidence, prints `wiki> 【Wikipedia参照・未検証】` with the article URL. **The Wikipedia text is not learned.**

- Existing canonical, corpus, and persona responses retain priority.
- Explicit Truth Gate BLOCK and stale internalized checkpoints never trigger this fallback.
- No article, no matching definition, invalid provenance or network failure: existing UNKNOWN rejection continues.
- No learning-log/history write, no `/sleep`, no Semantic Memory write or Truth promotion.
- The lookup is **exact-title**, not a broad search engine; no auto-retry or Wikipedia lead fallback to ungrounded generation.
- Default enabled for UNKNOWN concept definitions; set `LLM_CHA_AUTO_WIKIPEDIA=0` to disable.
- `/wiki PATH` explicit source-display command still works separately.

## Windows PowerShell

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_unknown_wikipedia_fallback_v0416.py test_wikipedia_chat_route_v0415.py test_wikipedia_answer_prefix_v04141.py
python verify_integration_v0366.py --gpu --legacy --timeout 240
python chat.py
```

Chat example (requires network access and a Wikipedia page whose exact title and introduction contain a supported definition):

```text
You> 小説とは
[wiki-lookup=HIT, source=Wikipedia, factual_truth=UNVERIFIED]
wiki> 【Wikipedia参照・未検証】
小説は文学の形式の一つである。
出典: https://ja.wikipedia.org/wiki/小説
[wiki-lookup=READ_ONLY, training=False, semantic_memory_writes=0]
```

Disable the network fallback before starting chat:

```powershell
$env:LLM_CHA_AUTO_WIKIPEDIA="0"
python chat.py
```

**Verification status**: code committed; mocked unit tests and existing GPU integration must be run locally. No empirical evidence is claimed until user reports them.
