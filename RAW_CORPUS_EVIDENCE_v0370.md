# LLM_CHA v0.3.7.0 — Evidence-first Raw Corpus Review

Experimental branch `v0.3.0`, stable `main` unchanged.

## Problem

For `量子力学` and `数学`, the active LLM_CHA runtime reports `RAW_CORPUS_ONLY`: the term occurs in `data/data-nagato.txt` but no trusted proposition/subject index/unified-memory entry exists. The dispatcher blocks generation as intended. `/sleep` cannot reliably fix this when there are no registered semantic propositions.

The corpus includes speculative, metaphorical, and subjective claims. Word occurrences are not evidence of factual validity. Promoting such passages automatically to VERIFIED would be unsafe and would defeat Truth Gate's purpose.

## First implementation: read-only candidate evidence

`raw_corpus_evidence_review_v0370.py` searches the original text, splits sentences conservatively, and reports:
- Source filename, line number, segment ordinal, excerpt, deterministic candidate ID
- `UNVERIFIED` and `PENDING_HUMAN_REVIEW` status
- Heuristic hedging/speculation markers when present
- Explicit confirmation that **no** corpus, knowledge index, truth gate, or checkpoint was changed

This is **not** a reliable general-purpose Japanese semantic proposition parser, factual verification, or a production learning pathway. It deliberately cannot promote candidates. The reviewer must assess what a passage literally asserts, whether it is an opinion or hypothesis, and whether trusted evidence independently supports it.

## Run

```powershell
git switch v0.3.0
git pull --ff-only origin v0.3.0
python -m unittest -v test_raw_corpus_evidence_review_v0370.py
python raw_corpus_evidence_review_v0370.py 量子力学 --report results/raw_corpus_quantum_v0370.json
python raw_corpus_evidence_review_v0370.py 数学 --report results/raw_corpus_math_v0370.json
python verify_integration_v0366.py --gpu --legacy --timeout 240
```

Expected nine new unit tests. Existing 264 test gate is unchanged; new evidence-review tests are separate for now.

## Next

Evaluate the extracted excerpts and add a reviewed, provenance-preserving candidate lifecycle that uses the existing semantic promotion/Truth Gate APIs and never silently authorizes speculative assertions. Internalization via `/sleep` should only be measured once knowledge admission is independently validated.
