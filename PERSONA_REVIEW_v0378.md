# LLM_CHA v0.3.7.8 — Real-Corpus Persona Role Quality Review

This is a **read-only** evaluation on raw `data/data-nagato.txt`, without changing any runtime, model, Truth Gate, or source files. It writes JSON and UTF-8-BOM CSV reports in `results/`.

- Every regex-extracted `MEANS_OF` candidate includes its source text, line/segment, subject, means, predicate, marker, and stable ID.
- Human classification is intentionally blank as `UNREVIEWED`. Review the CSV and mark each `CORRECT`, `AMBIGUOUS`, or `INCORRECT`, with a note; the tool does not pretend to know precision before adjudication.
- For each candidate, generate two exact source-oriented query probes, one by means and one by subject; report `source_hit_rate`. This is an **in-process query lookup coverage** test, **not** a full interactive `chat.py` E2E test and **not** the precision of semantic roles.
- `precision=null` until a separate human review scoring step is implemented.
- Where multiple candidate rows share a subject or means, selecting only the first can reduce exact source hit rate; that is an intended limitation to expose, not a reason to hide failures.

## PowerShell

```powershell
git switch v0.3.0
git pull --ff-only origin v0.3.0
python -m unittest -v test_persona_review_v0378.py test_persona_normalized_means_v0377.py
python persona_review_v0378.py --corpus data/data-nagato.txt --report results/persona_review_v0378.json --csv results/persona_review_v0378.csv
python verify_integration_v0366.py --gpu --legacy --timeout 240
```

Review the four previously measured candidates and send back the CSV or JSON. After classification, implement a scored extractor and a subprocess-based interactive E2E harness.
