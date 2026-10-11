# LLM_CHA v0.2.33.68 — Epistemic Classification Calibration

This is a deliberately **offline, read-only** scoring phase. Previous v0.2.33.67 detected 8 exact mentions of `量子力学` in the 33,180-character `data/data-nagato.txt` on the user's Windows host. This release creates a worksheet with one record per mention, original baseline labels, updated candidate labels, corpus SHA, byte offset and **`gold_labels: null`**.

The updated rules do **not** infer HYPOTHESIS from the bare technical term `可能性`. They remain lexical heuristics, not truth checks. A sentence can have more than one label.

## Execute on Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.68
git pull origin v0.2.33.68
python -m py_compile epistemic_calibration_v023368.py
python -m unittest -v test_epistemic_calibration_v023368.py test_corpus_context_classification_v023367.py
python epistemic_calibration_v023368.py
```

Expected worksheet: `results/epistemic_calibration_v023368.json`, without overwriting existing work.

Open a **copy** of that JSON and enter independently reviewed `gold_labels` arrays (e.g. `["ANALOGY","OPINION"]`) and change each `review_status` to `REVIEWED`. Evaluate reviewed rows with:

```powershell
python epistemic_calibration_v023368.py --score results/epistemic_calibration_v023368.json
```

Until at least one independent gold review, metrics remain `null`. When evaluated, micro precision/recall/F1 scores describe only reviewed rows, not generalization accuracy. The file SHA and context digest are included for audit; re-extract if the source corpus changes before review.

There are no changes to live `chat.py` commands, production SQLite candidate stores, Semantic Memory, Truth State, or LLM model weights. This phase precedes runtime policy changes.
