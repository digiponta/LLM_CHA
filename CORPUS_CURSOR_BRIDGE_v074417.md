# v0.7.44.17 — Corpus-to-Evidence Cursor Preflight

The existing `RetrievalFirstResult.records` contains
`CorpusMemoryRecord(subject, statement, relation, object_description,
source_text, source)`. There is **no proposition_id field** in the current
record schema. Evidence Cursor v0.7.44.16 needs a stable proposition ID.

The new `corpus_cursor_bridge_v074417.py` is deliberately fail-closed.
It reports `MISSING_ID` or `MISSING_SOURCE`, and returns no Evidence when
the identifier/provenance cannot be read. It does NOT invent IDs from
position or text. This stage does not change `chat.py` or the GUI.

## Verification

```powershell
git pull
python -m unittest -v test_corpus_cursor_bridge_v074417.py test_evidence_cursor_v074416.py
```

Expected: 13 tests. The legacy record test should pass by proving the
missing-ID condition is detected, not by pretending the cursor is ready.

## Next migration

1. Introduce an explicit immutable `proposition_id` when building the
   JSONL corpus-memory source records.
2. Preserve the source identifier and detect duplicates/conflicts.
3. Rebuild/upgrade the corpus-memory file with a compatibility policy.
4. Connect the bridge output and the cursor to `chat.py` after an end-to-end
   restore/migration test. Never promote UNVERIFIED facts during migration.
