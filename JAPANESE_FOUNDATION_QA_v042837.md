# LLM_CHA v0.4.28.37 — Japanese Foundation Data Import and QA Candidate Builder

Imported the original 4,600 independent Japanese utterances from the user-uploaded `japanese_foundation_v0218.txt` to `data/japanese_foundation_v0218.txt` on **v0.4.0**. Original sentence order preserved; do **not** pair adjacent lines as conversation turns or introduce these utterances as Nagato's biography/persona.

`build_japanese_foundation_qa_v042837.py` normalizes text, removes exact normalized duplicates, skips obvious personally identifying markers/URLs, and extracts only simple explicit first-person preferences of the form “私はXが好きです。” as **review-only positive QA candidates** with source file/line provenance. It is a deliberately **low-recall** baseline: most utterances should *not* become QA pairs. Every candidate has `human_verified: false` and `usage: TRAIN_CANDIDATE_ONLY`. No invented ground-truth negatives, no automatic hard-negative labeling, no independent evaluation set, no training/retraining in this release. This dataset cannot directly fix the Cross-Encoder's QA AUC without validated, diversified positives and verified negatives.

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m py_compile build_japanese_foundation_qa_v042837.py
python -m unittest -v test_build_japanese_foundation_qa_v042837.py

python build_japanese_foundation_qa_v042837.py `
  --input data/japanese_foundation_v0218.txt `
  --output results/japanese_foundation_qa_candidates_v042837.json
```

Expected **6** focused tests; Windows verification pending. The new output includes `source_lines`, `unique_normalized_lines`, `pii_filtered_lines`, `candidate_count`, `source_sha256` and `candidates`. Compare counts and manually inspect candidates before introducing a QA learner. The source may contain personal details, first-person life stories, and time-sensitive assertions. Separately audit licensing/attribution and privacy before redistributing or training beyond authorized use.

No changes to production Truth Gate, generator, Semantic Memory, /sleep, /train, or chat.py, and no edits to main.
