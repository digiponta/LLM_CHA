# LLM_CHA v0.4.6 — Wikipedia Candidate Acquisition (read-only)

This is **Stage 1** of external knowledge acquisition. `wikipedia_candidate_v0406.py` performs an explicit, one-shot **Japanese Wikipedia MediaWiki REST search** at `/w/rest.php/v1/search/page`. It returns at most five search candidates with title, description, plain-text search excerpt, article link, retrieval timestamp and provenance.

All candidates are `UNVERIFIED`, `PENDING_REVIEW`, and `eligible_for_training=false`. Search excerpts are **not full articles**, not a guarantee of truth and not automatically valid answers. This feature **does not modify** `chat.py`, existing UNKNOWN routing, Persona Memory, Truth Gate, training queues, checkpoints, or `/sleep`. It makes no automatic network calls from chat. A named report path is optional and writes only diagnostic JSON; report content should not be auto-promoted. It uses only Python standard library. Failures are explicit and do not fall back to invented Wikipedia results.

The endpoint and search result structure are documented by MediaWiki:
https://www.mediawiki.org/wiki/API:REST_API/Reference

## PowerShell

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_wikipedia_candidate_v0406.py
python wikipedia_candidate_v0406.py 小説 --report results/wikipedia_candidate_v0406_novel.json
python verify_integration_v0366.py --gpu --legacy --timeout 240
```

Validate the title/description/excerpt and click the source article before any human approval. Live Wikipedia availability and the observed result count depend on connectivity; network success is **not** proven by mocked unit tests. If connectivity or the API fails, diagnose HTTP status/network policies and do not write fabricated candidate data.

Later v0.4.7+ may add a separate reviewed candidate lifecycle, source freshness and license metadata, and controlled promotion to Semantic Memory. Respect Wikimedia access policy and content licensing for any future persistent copies or training datasets.
