# LLM_CHA v0.9.7.55 — Semantic Context and Japanese Surface

## Changes

- Adds conservative conversation-local carryover for unfinished composition inquiries, e.g. 「スファレライトの成分は」 → 「化学組成を知りたい」. It keeps the subject in the follow-up and **does not invent a composition**; the response explicitly requests verified source information rather than asserting unsupported chemistry.
- Fixes Preference Intent response duplication: 「宝石としてのスファレライトが好きです」 → 「宝石としてのスファレライトが好きなんだね。」
- Adds short evaluation acknowledgement for 「きれいです」「美しいです」 → 「そう。」
- All changes are gated by existing `--final-guard` where relevant. Context is transient and memory/weights/truth records remain unchanged.
- The Wikipedia alias/source equivalence gate and truly grounded composition-answer retrieval remain future work. Do not treat a search selection alone as verified equivalence.

## Windows PowerShell

```powershell
git fetch origin
git switch --track origin/v0.9.7.55
python -m unittest -v test_semantic_context_surface_v09755.py test_preference_intent_v09750.py test_opinion_intent_v09754.py
python chat_window_v061.py --final-guard --gui-only-input
```

Expected 24 tests (8 + 6 + 10), then exercise the sphalerite conversation in the GUI. The topic bridge is deliberately narrow, not general anaphora resolution.