# LLM_CHA v0.4.28.1 — Persona Diagnostic Score Hardening

Fix: `chat.py` could exit with `ValueError: invalid agreement` after generation. The read-only `diagnose_relevance` function incorrectly assumed cosine-based semantic agreement was always 0..1. Cosine agreement is valid in -1..1.

Changes:
- Accept finite numeric lexical agreement 0..1 and finite numeric semantic agreement -1..1.
- For invalid diagnostic scores (NaN, infinity, nonnumeric, out of expected range), return `diagnostic_scores_valid=False`, `relevance_warning=True`; do not crash.
- Shadow evaluation does not attempt score threshold comparisons when inputs are invalid.
- No modifications to `chat.py`, generation, Truth Gate, knowledge provenance, runtime acceptance, `/sleep`, training, or memory.

## Windows verification
```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_persona_relevance_hardening_v04281.py test_persona_response_shadow_v0421.py
python verify_integration_v0366.py --gpu --legacy --timeout 240
python chat.py
```

Enter `名前を教えてください。` and verify the previous exception no longer occurs. This does not prove the generated answer is correct.

Note: The existing opt-in quality capture validates scores in 0..1 and can reject negative semantic cosine values. Capture errors must not affect the live answer; expansion of capture schemas is out of scope here.
