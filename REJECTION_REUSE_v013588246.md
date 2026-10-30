# v0.13.58.82.46 — Rejection reuse and concept query normalization

- Japanese explicit concept questions such as `宇宙を説明してください` are sent to CLI as `宇宙とは`. The original text remains displayed. This is a lexical normalization, not general semantic equivalence.
- Evidence-gated rejected candidates are remembered in `data/rejected_evidence_cache_v013588246.jsonl` keyed on topic, exact evidence excerpt, and checkpoint file path/size/mtime. If the same model and evidence are encountered again, the GUI skips the repeated LLM generation and displays the fallback plus the prior rejected candidate. Model changes invalidate the cache key. An unknown model checkpoint disables reuse.
- `/negstats` shows how many negative signals have been recorded and how many remain `NOT_TRAINED`. It is read-only.
- `/good` remains disabled; positive learning and negative weight updates are not automatically executed. This release only reuses prior gate decisions at inference.
- `CORPUS_MEMORY` and `CANONICAL` provenance are not yet machine-readable in the current GUI; normal CLI responses retain `採否未判定`.

## Windows
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.46-rejection-reuse
python -m unittest -v test_rejection_reuse_v013588246.py test_negative_only_v013588244.py
python chat_gui.py
```

Test questions: `宇宙を説明してください`, `宇宙とは`, `もっと詳しく`, `もっと詳しく`, `/negstats`. Verify diagnostics `[Concept Query Normalized]`, `[Rejected Candidate Reused]` where evidence and model are identical, and negative counts. Note: old bad responses recorded before this version are not automatically imported into the cache, so the first rejected response in this branch is still generated.
