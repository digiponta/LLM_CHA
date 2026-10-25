# LLM_CHA v0.9.7.2 — Web Knowledge Extraction (review-only)

This experimental stage converts existing `web_pending_v097.jsonl` records
into source-linked **quotation candidates** in a separate JSONL file.
It does not infer structured subject/predicate facts, semantic vectors,
scientific truth, license permission, or training readiness.

Each candidate carries a stable ID, original text, provenance URL/title,
retrieval timestamp, source hash, unverified status and mandatory reviews.
It intentionally does not connect to existing approval queues or `/sleep`.
Duplicates within the imported data are deduplicated by source and quote.

## Windows PowerShell

```powershell
git fetch origin
git switch --track origin/v0.9.7.2
python -m unittest -v test_extract_web_candidates_v0972.py test_web_acquisition_v097.py test_web_robots_404_v0971.py
python extract_web_candidates_v0972.py data/web_pending_v097.jsonl data/web_semantic_candidates_v0972.jsonl
```

The page https://example.org/ is only a network test and may yield **zero**
candidates because its text is short or has no suitable sentence boundaries.
Try a reviewed, permitted, content-rich source to test extraction quality.
Do not treat Web text as executable instructions, trusted facts, or
automatically permitted training data.

Note: the v0.9.7.1 transport retains an acknowledged DNS-rebinding risk.
Do not deploy as an untrusted public crawling service; replace its network
transport with pinned-address connections and restricted egress before that.
