# LLM_CHA v0.2.33.66 — Source-Anchored Corpus Candidate Extraction

This branch adds a **read-only UTF-8 corpus scanner** that extracts only restricted, complete structural propositions whose subject matches an approved session reference → concept mapping. It records **full-file SHA-256, byte start/end offsets, and snippet SHA-256** for every match in an independent SQLite review store.

Every imported candidate begins as `PENDING`, and human decisions are scoped to the approved context/concept. Reviews fail closed if the original file contents have changed since extraction. `APPROVED` is **not** a truth assertion; there are no writes to Semantic Memory, Truth State, or model weights.

## Windows PowerShell
```powershell
git fetch origin
git switch v0.2.33.66
git pull origin v0.2.33.66
python -m py_compile chat.py corpus_candidate_extraction_v023366.py
python -m unittest -v test_corpus_candidate_extraction_v023366.py test_proposition_candidate_lifecycle_v023365.py
python chat.py --session-reference-memory
```

After approving `cursor` and the existing mapping `cursor → 量子力学`:

```text
/refcorpus scan
/refcorpus list
/refcorpus approve corpus-...
/refcorpus list
/refcoverage
```

If `data/data-nagato.txt` contains no sentence recognized by the conservative grammar with the exact subject `量子力学`, scanning finds **0 candidates**; this is not proof that the concept is absent from the full raw corpus. Unsupported paraphrases and complex sentences remain excluded. The source scanner does not silently import semantic facts or set `TRUE`.

The v0.2.33.66 ten-test suite covers UTF-8 byte offsets, stable source hashes, deduplication, explicit approval, source-change refusal, context/concept separation, decoding failures, limits, exact-subject filtering and source immutability.
