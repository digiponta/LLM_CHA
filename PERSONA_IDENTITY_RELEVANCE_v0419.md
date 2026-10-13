# LLM_CHA v0.4.19 — Persona Identity and Answer Relevance Guard

Purpose: address the real transcript regression `貴方は誰 → AI> 連載後半は対話。 |読切・` that was accepted despite probe agreement=0.032 and semantic agreement=0.881.

Changes:
1. `persona_identity_guard_v0419.py`: narrow, deterministic Japanese identity-intent patterns (e.g. `貴方は誰`, `あなたは誰ですか`, `名前を教えて`). Replies `persona> 長門有希。` from explicitly configured Nagato persona. No general topical, third-party or fragment route. Does not train or write memory. Profile selection is not yet wired here; the current chat runtime is fixed to the Nagato checkpoint.
2. `chat.py`: identity query handled before normal knowledge routing and model generation. Existing Wikipedia/Truth Gate branches are not changed.
3. `persona_answer_relevance_v0419.py`: **diagnostics only** after model generation: warns for low probe agreement or identity mismatch even when semantic agreement is high. It does not independently reject general conversation, which requires further holdout calibration.
4. `test_persona_identity_guard_v0419.py`: identity, non-identity, safety and diagnostic coverage.

Known limitation: the identity route is a deterministic configured-profile response, not evidence of model-weight learning or semantic self-awareness. `persona>` here means a profile-governed answer. Further persona switch support needs explicit integration and tests.

Windows PowerShell:

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_persona_identity_guard_v0419.py test_article_proposition_alignment_v0418.py test_wikipedia_retrieval_diagnostics_v0417.py
python verify_integration_v0366.py --gpu --legacy --timeout 240
python chat.py
```

Test interactive `貴方は誰`, `あなたは誰ですか`, `長門`, `貴方は`, `化学とは`, `CPUとは`. No Windows runtime pass claim is made before logs arrive.
