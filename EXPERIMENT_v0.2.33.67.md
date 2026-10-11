# v0.2.33.67 — Corpus Context-Aware Extraction & Epistemic Classification

**Aim:** count and preserve *every occurrence* of a concept even when the concept is not the grammatical subject. Exact UTF-8 byte offset and full-file / context SHA-256 anchor each mention; preliminary lexical labels indicate writing style rather than factual correctness.

## Windows PowerShell
```powershell
git fetch origin
git switch v0.2.33.67
git pull origin v0.2.33.67
python -m py_compile chat.py corpus_context_classification_v023367.py
python -m unittest -v test_corpus_context_classification_v023367.py test_sqlite_connection_cleanup_v0233661.py
python chat.py --session-reference-memory
```

After approved `cursor → 量子力学`, enter:
```text
/refmentions scan
/refmentions list
/refcorpus scan
/refcoverage
```

For the previously reported `data/data-nagato.txt` (33,180 characters, 8 occurrences of `量子力学`), the expected mention count is 8 **if the file contents and mapping are unchanged**. Unlike v66's statement parser, it does not require the concept as sentence subject. This is not a count of true propositions.

Labels:
- `HYPOTHESIS`: tentative markers such as `かもしれない`, `可能性`, `多分`
- `ANALOGY`: `ようなもの`, `アナロジ`, `類似`
- `OPINION`: `見方`, `観点`, `考えると`
- `STRUCTURAL_CANDIDATE`: accepted restricted proposition grammar with no above marker
- `CONTEXT_ONLY`: otherwise

Labels may overlap and are **heuristics only**. Their absence is not evidence of objective truth. Records remain `PENDING`; there is no automatic human approval, Truth State change, Semantic Memory mutation, or model learning. The original file and all existing v66 SQLite candidate history are preserved.
