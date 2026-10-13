# LLM_CHA v0.4.17 — Wikipedia retrieval diagnostics

Changes to the automatic UNKNOWN Wikipedia fallback on the `v0.4.0` branch:
- Distinguish `FETCH_ERROR`, `ARTICLE_REJECTED_OR_NOT_FOUND`, `EVIDENCE_REJECTED`, `NO_DEFINITION`, `NOT_DEFINITION_QUERY`, and `HIT`.
- After valid article retrieval but no v0.4.12 extractive definition, show v0.4.14 heuristic boundary classes for diagnostic purposes only.
- Preserve existing exact-title requirement, source hash validation, Wikipedia attribution, UNVERIFIED state, and no auto-learning, Semantic Memory writes or truth promotion.
- Failed lookups still reach the old `AI> 未学習です` route.

The previous v0.4.16 implementation silently returned None when no definition was extracted. In the user's earlier run, `化学とは` returned `未学習です` without an exception. This version makes the failure branch observable. It does **not** relax the extractor, assume article existence, or claim to have confirmed a particular failure reason before the actual runtime test.

## Run in PowerShell

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_wikipedia_retrieval_diagnostics_v0417.py test_unknown_wikipedia_fallback_v0416.py test_wikipedia_chat_route_v0415.py test_wikipedia_answer_prefix_v04141.py
python verify_integration_v0366.py --gpu --legacy --timeout 240
python chat.py
```

Try `化学とは`, `小説とは`, `哲学とは`; inspect the `[wiki-lookup=..., reason=..., boundary=...]` output. Subsequent improvements should add article-title search/redirect evaluation and broader definition patterns only with separate tests and evidence checks.
