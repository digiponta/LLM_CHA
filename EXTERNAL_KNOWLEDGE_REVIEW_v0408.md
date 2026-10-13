# LLM_CHA v0.4.8 — External Knowledge Review

Adds manual review to the **isolated** v0.4.7 Wikipedia candidate store. Nothing is promoted to Semantic Memory or labeled TRUE. Review decisions: `APPROVED_FOR_REVIEW_ONLY`, `REJECTED`, `PENDING_REVIEW`. Approval only records an operator's judgement to proceed with further research; it does not validate the article's scientific accuracy.

Review requires candidate ID, matching **current content SHA256**, reviewer identifier and nonempty reason. Each action appends an audit row with old/new decision, reviewer, reason, URL, content hash, and UTC time. Candidate content changes on subsequent v0.4.7 imports reset state to `NEEDS_REREVIEW`; a stale SHA review is refused. Writes are atomic but **not locked for concurrency**; one writer only, and retain backups of the JSON store. Reviews are not cryptographically signed and reviewer identity is only user-supplied text, so this is an experimental manual audit, not a security-grade identity system.

## PowerShell validation

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_external_candidate_review_v0408.py test_external_candidate_store_v0407.py
python external_candidate_review_v0408.py --store results/external_candidate_store_v0407.json list
python verify_integration_v0366.py --gpu --legacy --timeout 240
```

To review a specific candidate, first manually inspect its source Wikipedia URL and verify its title, relevancy and quality. **Do not approve solely because the search matched.** Copy its ID and SHA256 exactly from the list command:

```powershell
python external_candidate_review_v0408.py --store results/external_candidate_store_v0407.json review --id <24_hex_candidate_id> --sha256 <64_hex_current_content_hash> --decision REJECTED --reviewer local-reviewer --reason "検索結果の断片だけでは定義の妥当性を確認できない"
```

Replace placeholders with actual values; do not include the angle brackets in PowerShell. It is safe to defer reviews until full-article evidence is available. List is read-only; review changes only the isolated JSON store. v0.4.8 does not change `chat.py`, the Truth Gate, model weights, `/sleep`, or original Persona corpus.

Later versions should verify article-level evidence, licensing and source freshness before any promotion workflow.
