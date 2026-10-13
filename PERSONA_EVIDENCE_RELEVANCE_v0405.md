# LLM_CHA v0.4.5 — Persona Evidence Relevance (diagnostic)

This release adds **read-only** relevance diagnostics for Persona source excerpts. It distinguishes a focus concept as syntactic topic versus a secondary literal mention and records a narrow definition-style pattern, predicate cues, and a fragment-length heuristic. These heuristics are transparent, deterministic and **not a learned, calibrated semantic relevance score**; context verification and human evaluation are not implemented.

The real v0.4.4 trace demonstrated that 「文学とは」 retrieves 「数学は、文学の分類」 as a **related quote**, not a definition. The heuristic should flag 文学 as a secondary mention in this excerpt. Source material may make questionable claims: diagnostic scores **never** imply scientific factual validity.

No changes to chat.py, Truth Gate, model weights, or the corpus. The v0.4.4 opt-in UNKNOWN quotation behaves as before. Do not use heuristic scores to accept or reject production Persona retrieval until human-labeled evaluation and calibration.

## PowerShell

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_persona_evidence_relevance_v0405.py test_persona_unknown_quote_v0404.py
python persona_evidence_relevance_v0405.py --corpus data/data-nagato.txt --report results/persona_evidence_relevance_v0405.json
python verify_integration_v0366.py --gpu --legacy --timeout 240
```

Share the JSON report for comparison. Expected direction: a literal secondary mention such as 「数学は、文学の分類」 is not treated as a validated definition for 文学. The actual report and test results remain to be measured locally.
