# LLM_CHA v0.2.33.35 — Interactive Unknown Resolution (isolated prototype)

## Aim

Provide a **user-clarification route** for ambiguous referents while keeping algorithmic copying of unknown token IDs separate. A model's inability to copy unfamiliar IDs is a generalization failure, **not** a reason to ask the user for the correct token sequence. Clarification is useful only when user-specific intent, referent or constraints are genuinely underspecified.

## Experiment boundary

`interactive_unknown_resolution_v023335.py` is an **isolated deterministic mock adapter**, not integrated with production DSS, Semantic Memory or Transformer. It introduces:

- ambiguous prior-experiment reference detection
- pending clarification session with two supported choices
- a candidate stage and **explicit approval** before committing to local memory
- rejection, cancellation, bounded retries and abstention
- reuse of approved local meaning so the same user need not answer again
- a JSON demo transcript with candidate provenance/status

This version deliberately does **not** write to actual Semantic Memory, train any LLM, or interpret arbitrary natural language. The local registry is in-memory only and persists solely for a single demo process.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.35
git pull origin v0.2.33.35
python -m py_compile interactive_unknown_resolution_v023335.py
python -m unittest -v test_interactive_unknown_resolution_v023335.py
python interactive_unknown_resolution_v023335.py --demo
```

Outputs `results/interactive_unknown_resolution_v023335.json` once; refuses overwrite. Later work should add a narrowly scoped DSS adapter and Semantic Memory **candidate** interface after API inspection, train/test clarification policy on independent dialog data, and keep a safety-preserving no-question fallback when unresolved.

### Follow-on workstream

`Script-Conditioned Cursor / EOS Calibration` stays separate, because it addresses state-dependent synthetic sequence generation rather than missing intent. It is **not implemented by this branch**. No stable components or existing checkpoints are altered.
