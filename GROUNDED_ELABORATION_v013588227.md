# v0.13.58.82.27 Context-Grounded Elaboration

The GUI now handles `もう少し詳しく` after a recorded/recovered topic by asynchronously searching Japanese Wikipedia, selecting a matching article title, and displaying up to four excerpt sentences with a source URL and an EXTERNAL_UNVERIFIED label. It does not rephrase speculative LLM output as scientific truth. If no matching evidence exists or retrieval fails, it explicitly declines unsupported elaboration.

The prior topic answer remains available in session context, while the source for new elaboration is distinguished from the older LLM generation. This release also corrects Wikipedia fallback history capture: actual results use status `HIT`, not only `FOUND` etc.

This is an evidence-grounded elaboration stage, **not yet** context-conditioned Transformer generation. It does not train or modify the LLM, promote Wikipedia to trusted Semantic Memory, or store the user's history.

## Validation (PowerShell)
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.27-grounded-elaboration
python -m unittest -v test_grounded_elaboration_v013588227.py test_topic_answer_context_v013588226.py
python chat_gui.py
```
Dialog: `宇宙とは` -> `CPU` -> `宇宙の話に戻って` -> `もう少し詳しく`. The last answer should include a Wikipedia source (if accessible and matching) rather than just asking a question. `量子力学とは` -> `もう少し詳しく` should also work when Wikipedia fallback was successful.

Known limits: Wikipedia excerpts are externally sourced but not independently verified; title match and sentence selection are conservative heuristics; this is not an LLM-driven new explanatory generation or scientific claim classifier.
