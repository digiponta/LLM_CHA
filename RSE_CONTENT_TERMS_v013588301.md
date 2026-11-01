# RSE Phase 1.1 — Content-term matching

This experiment addresses v0.13.58.83.00's matches on generic どう and とは. It adds Sudachi morphology and content coverage, defaults to requiring every extracted content keyword to match an indexed source question. No LLM training, generation, or chat.py changes.

PowerShell:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.83.01-rse-content-terms
python -m unittest -v test_rse_content_terms_v013588301.py
python rse_content_terms_v013588301.py --question "最近どう？"
python rse_content_terms_v013588301.py --question "スファレライトとは？"
```

Expected: some general social prompts have zero content terms and abstain. For named entities absent in the source corpus, abstention should occur. The current stopword/part-of-speech heuristic is a baseline, not real semantic alignment; a content match may still yield an unsuitable response. Preserve Semantic Memory precedence for known factual topics and never present a RealPersonaChat participant's personal experiences as the model's experiences.
