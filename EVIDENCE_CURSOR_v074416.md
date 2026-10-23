# LLM_CHA v0.7.44.16 — Evidence-Aware Follow-up Cursor

Adds `evidence_cursor_v074416.py` as an isolated, source-preserving
component. It tracks explicit proposition IDs and skips records whose
complete original text is already contained in the first response.

## Requirements and constraints

- Only same-topic, provenance-bearing UNVERIFIED records may be offered.
- No proposition ID is returned more than once in the same cursor session.
- Topic reset clears previous presented IDs, preventing unrelated leakage.
- If all evidence was displayed initially, there is no new evidence to offer.
- Raw evidence text and provenance are not changed. No auto-approval or learning.
- The cursor does **not** invent detail when no evidence exists.

## Verify

```powershell
git pull
python -m unittest -v test_evidence_cursor_v074416.py
```

This stage intentionally does not alter `chat.py`. The following
integration stage must obtain real proposition IDs and provenance from
the corpus retrieval API, not synthesize IDs from generated text. A
future runtime wiring must preserve existing Truth Gate and Wikipedia
follow-up priority. Validation on the user's Windows GPU remains pending.
