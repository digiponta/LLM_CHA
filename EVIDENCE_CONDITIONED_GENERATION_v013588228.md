# v0.13.58.82.28 — Evidence-Conditioned LLM Generation

When a user returns to a prior topic and asks `もう少し詳しく`, the GUI derives a focused retrieval query from the topic and previous answer. E.g. `宇宙` plus `膨張` => `宇宙膨張`. A background Wikipedia lookup returns an explicitly EXTERNAL_UNVERIFIED excerpt and URL. If evidence is found and `chat.py` is running, the GUI supplies a short evidence-bound prompt to the existing local Transformer and reads back its candidate.

A conservative post-generation gate checks for unknown, malformed, unsupported, or speculative content. Only a verbatim source-supported candidate passes; otherwise an attributed evidence excerpt is displayed. This intentionally sacrifices generation fluency for claim safety and avoids presenting speculative LLM output as established physics. Wikipedia data is not promoted into Trusted Semantic Memory or trained into weights. No network requests run on the Tk main thread.

## Limits
The model may not obey natural-language instructions, may reject all generated candidates, or may not treat a long prompt well (context 512). Consequently, the source-excerpt fallback is expected in many cases. The lexical gate is **not** a semantic entailment verifier. The LLM candidate is not guaranteed to generate novel factually supported prose; this release establishes the generation-and-validation interface for later evaluation. Existing GUI FIFO matching assumes serial CLI inference; concurrent requests should be tested carefully.

## Validation
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.28-evidence-conditioned-generation
python -m unittest -v test_evidence_conditioned_generation_v013588228.py test_grounded_elaboration_v013588227.py test_topic_answer_context_v013588226.py
python chat_gui.py
```

Dialogue: `宇宙とは` → `CPU` → `宇宙の話に戻って` → `もう少し詳しく`. Check `[Evidence-Conditioned LLM]` and `[Evidence Gate]` in the diagnostics. Next, `量子力学とは` → `もう少し詳しく`. Inspect the displayed sources and rejected generation handling.
