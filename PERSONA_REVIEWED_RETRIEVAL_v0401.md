# LLM_CHA v0.4.1 — Opt-in Human-Reviewed MEANS_OF Retrieval

Development only on `v0.4.0`. Protected baseline `v0.3.7.8-verified` and `main` are unchanged.

The reviewed-only lookup uses the original `data/data-nagato.txt` and a manually edited `persona_review_v0378.csv`. The scorer strictly checks candidate IDs, coordinates, original text, role values, unique records, and verdicts. Only `CORRECT` results can match in the new route. Output is **verbatim source quotation**, with `factual_truth=NOT_ASSESSED`; review is not scientific truth verification.

Opt-in mode skips both older unreviewed MEANS_OF routes in `chat.py`, and requires the existing Truth Gate to permit the query focus, subject, and means. The new route returns no match for missing, unreviewed, ambiguous or incorrect candidates, or for ambiguous multiple matches. On CSV invalidity, `chat.py` reports a BLOCK diagnostic and continues to other unchanged chat routes; **this is not a global no-answer gate**. Under the default (disabled) setting, legacy behavior remains unchanged.

## PowerShell

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_persona_reviewed_retrieval_v0401.py test_persona_review_score_v0400.py
python verify_integration_v0366.py --gpu --legacy --timeout 240

# After reviewing the four candidates and editing only verdict/note:
$env:LLM_CHA_REVIEWED_MEANS_ONLY="1"
$env:LLM_CHA_REVIEW_CSV="results/persona_review_v0378.csv"
python chat.py
```

Without any CORRECT reviews, zero reviewed-candidate hits are expected. The previous 4 candidates are all UNREVIEWED; do not fabricate positive retrieval outcomes. Full subprocess/chat E2E acceptance remains to be measured.
