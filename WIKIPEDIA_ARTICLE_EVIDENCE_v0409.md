# LLM_CHA v0.4.9 — Wikipedia Article Lead Evidence (experimental)

Standalone read-only tool `wikipedia_article_evidence_v0409.py`. Looks up an existing v0.4.7 stored Wikipedia candidate by ID and current candidate-content SHA256, then uses Japanese MediaWiki Action API `action=query&prop=extracts|revisions&exintro=1&explaintext=1&rvprop=ids&formatversion=2` to acquire the current **plain-text introduction**. Returns article title, page ID, currently reported revision ID, short article text (at most 6000 characters), SHA256 of that extract, original candidate ID/hash, URL, and time.

**Limitations:** This is not the full article, independent fact checking, reliable proposition extraction, or a frozen historical revision fetch. The extract and revision metadata are queried together, but the content is not checked against an immutable revision. Accordingly `revision_content_verified=false`, `human_article_reviewed=false`, and `factual_truth=UNVERIFIED`. Extracts are subject to formatting, caching and API behavior. The tool rejects missing/renamed articles and unresolved title mismatches instead of silently using another topic. API errors must be inspected. Article extracts are third-party content; preserve attribution and comply with Wikimedia licensing before redistribution/training. This version does **not** review, promote, learn, or alter Semantic Memory, Truth Gate, `/sleep`, `chat.py`, or the candidate store. An optional report path writes to an isolated JSON report and should not be set to any existing store path.

## PowerShell

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_wikipedia_article_evidence_v0409.py test_external_candidate_review_v0408.py
python external_candidate_review_v0408.py --store results/external_candidate_store_v0407.json list
```

For the previously reported `小説` candidate, whose SHA256 was recorded in the user's actual v0.4.8 output:

```powershell
python wikipedia_article_evidence_v0409.py `
  --store results/external_candidate_store_v0407.json `
  --id 9d15803256a93238619bcc56 `
  --sha256 97da51237898e7f1c3a4c63ca1261acc374c9fb5c73efa120b3ad99a9ccc2e9e `
  --report results/wikipedia_article_evidence_v0409_novel.json
python verify_integration_v0366.py --gpu --legacy --timeout 240
```

If the candidate has changed since v0.4.8, re-list and use the current ID and content hash, rather than bypassing the check. Share JSON/logs for evaluation before moving to a review of specific article-supported propositions.
