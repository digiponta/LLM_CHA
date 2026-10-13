# LLM_CHA v0.4.10 — Article-to-Proposition Evidence Alignment

Adds an **offline, read-only, extractive alignment diagnostic** for v0.4.9 Wikipedia article evidence JSON. This version deliberately supports a narrow Japanese template: `<concept>（optional balanced metadata）は、<predicate>である。` or `<concept>は<predicate>だ。`. No machine-learned semantic parsing, no paraphrase and no inference. Nested Japanese parenthetical forms found in the real `小説` Wikipedia introduction are handled. A candidate's `evidence_start`, `evidence_end` (Python character offsets), `evidence_text`, subject and predicate are returned. A mismatch between SHA256 and original `lead_extract` is rejected. Missing patterns return zero propositions instead of inventing an answer.

All results are `UNVERIFIED` and `PENDING_REVIEW`; `revision_content_verified=false`, `truth_promotions=0`, `semantic_memory_writes=0`, and `training_enabled=false`. The result indicates **literal article support**, not truth or human approval. The v0.4.9 revision ID is only provenance metadata, not a verified frozen revision. This does not modify `chat.py`, Persona/semantic memory, model weights, review store, Truth Gate, or `/sleep`.

## Windows PowerShell verification

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0

python -m unittest -v test_article_proposition_alignment_v0410.py test_wikipedia_article_evidence_v0409.py

python article_proposition_alignment_v0410.py `
  --evidence results/wikipedia_article_evidence_v0409_novel.json `
  --report results/article_proposition_alignment_v0410_novel.json

python verify_integration_v0366.py --gpu --legacy --timeout 240
```

The real previous extract began `小説（しょうせつ、英: fiction ...）は、文学の形式の一つである。`. This should produce one exact-span proposition with subject `小説` and predicate `文学の形式の一つである`. This is a **prediction to test**, not a measured v0.4.10 result.

## Next

Future work should test variation in Japanese definition sentences, source-revision consistency, and human-reviewed alignment quality on a held-out corpus before enabling any optional runtime integration. Preserve attribution and Wikipedia licensing as applicable.
