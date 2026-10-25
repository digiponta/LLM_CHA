# v0.9.1 — Corpus-first response planning

Experimental read-only component. It provides a plan for routing explicit
knowledge questions through the Nagato corpus before Wikipedia fallback.
The script does not alter `chat.py`, model weights, or Semantic Memory.

```powershell
git fetch origin
git switch --track origin/v0.9.1
python -m unittest -v test_corpus_answer_plan_v091.py
python corpus_answer_plan_v091.py "量子力学とは"
```

If the corpus mentions quantum mechanics without providing a direct definition,
the expected route is `CORPUS_THEN_EXTERNAL_DEFINITION`. Retain original
provenance and mark those passages as unverified. The actual conversational
runtime is not yet wired to this module; route selection, topical evidence
ranking, and persona rendering still require integration tests.
