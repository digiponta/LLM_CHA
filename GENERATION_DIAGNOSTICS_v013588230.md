# LLM_CHA v0.13.58.82.30 — Evidence-Conditioned Generation Diagnostics

The GUI measures how often the existing Transformer candidate passes or fails the conservative Evidence Gate. New chat commands:

- `/genstats`: cases, gate counts, candidate acceptance, unknown, evidence rejection and fallback rates.
- `/gencompare`: identified baseline (attributed Wikipedia excerpt) versus candidate pipeline; explicit note that relative quality is **not** established without independent human paired evaluation.
- `/genstats reset`: clear the current in-process aggregate.

Rates use all observed evidence-conditioned elaboration attempts as denominator. A missing article is counted as NO_EVIDENCE; unavailable inference model is NO_MODEL; candidate rejection uses existing gate states. Each session event stores classification, source state, topic and character counts, but not candidate/answer text. Data are not automatically persisted or trained. GUI restart resets counters.

## Windows verification

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.30-generation-diagnostics
python -m unittest -v test_generation_diagnostics_v013588230.py test_single_turn_conditioned_v013588229.py test_evidence_conditioned_generation_v013588228.py
python chat_gui.py
```

Dialog: `宇宙とは` → `CPU` → `宇宙の話に戻って` → `もう少し詳しく` → `/genstats` → `/gencompare`. Inspect the diagnostic tab for `[Evidence Gate]` and report metrics.

Limits: metrics measure pipeline selection, **not** independent factual accuracy, user satisfaction or semantic entailment. This release does not yet report latency or create paired human-rated quality benchmark cases.
