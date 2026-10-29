# LLM_CHA v0.13.58.82.11 — Unified Dialogue Context (initial)

This increment adds a bounded in-memory multi-topic index and connects it to GUI routing. It supports an explicit return to an earlier gem topic:

1. 「スファレライトをぐぐって」 → active topic = スファレライト.
2. 「スターバックスをぐぐって」 → active topic = スターバックス; prior gem retained.
3. 「さっきの宝石の黄色が好き」 → restore スファレライト for both Evidence and Preference contexts; respond to the color preference.

The resolver is conservative and keyword-based. It does **not** yet merge all Evidence, Preference and Experience state into a single representation, solve arbitrary pronouns, or persist user preferences. Unrecognized utterances continue through the existing pipeline. External evidence remains unverified; no automatic learning or Semantic Memory promotion.

## Windows regression
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.11-unified-dialogue-context
python -m unittest -v test_unified_dialogue_context_v013588211.py test_preference_dialogue_v013588210.py test_causal_evidence_retrieval_v01358829.py
python chat_gui.py
```
