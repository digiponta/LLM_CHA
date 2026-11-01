# v0.13.58.83.03 — RSE intent candidate shortlist

This phase adds an *audit-only* shortlist of RealPersonaChat replies whose **source questions** match the detected social intent. Answers are never automatically returned to the user; candidates contain IDs, lengths, and a coarse personal-claim warning. `--show-answers` exposes source text locally only, and stored JSON reports never include the source answer.

PowerShell:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.83.03-intent-candidate-selection
python -m unittest -v test_rse_intent_candidates_v013588303.py test_rse_intent_v013588302.py
python rse_intent_candidates_v013588303.py --question "最近どう？"
python rse_intent_candidates_v013588303.py --question "少し話さない？"
python rse_intent_candidates_v013588303.py --question "今何してる？"
python rse_intent_candidates_v013588303.py --question "スファレライトとは？"
```

For manual inspection only, add `--show-answers`. Do not upload unredacted dialogue transcripts.

The shortlist uses deterministic sorting by the absence of obvious first-person claims, answer length and source ID. This **is not** semantic relevance ranking, and the regular-expression risk flag is neither a privacy audit nor an identity protection guarantee. A response copied from CP may still be inappropriate even when the flag is false. If no candidate matches, the original assistant-safe template remains available for further experimentation. Factual topics defer to Semantic Memory. LLM expansion and live chat integration are out of scope.
