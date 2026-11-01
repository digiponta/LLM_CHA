# v0.13.58.83.12 — Semantic Theme / explicit UNLEARNED

This branch implements an **experimental**, standalone theme + question/answer relation selector. It is not integrated into chat.py or Semantic Memory yet.

Principles:
1. A common theme is needed but not sufficient. Both question intent and time slot must match.
2. The response relationship must make sense (invitation -> acceptance and topic question, greeting -> returned greeting).
3. Obvious third-party autobiographical statements are conservatively blocked.
4. If there is no single supported safe candidate, return exactly `未学習です`, and status `UNLEARNED`. Never fabricate via model decoding or use the prior canned RSE fallback in this experimental path.
5. `UNLEARNED` means no accepted answer in the current candidate set; it is not proof that the underlying trained model lacks knowledge.

Windows:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.83.12-semantic-theme-unlearned
python -m unittest -v test_rse_semantic_theme_v013588312.py
python rse_semantic_theme_v013588312.py --query "少しお話ししませんか？"
python rse_semantic_theme_v013588312.py --query "今何してる？"
python rse_semantic_theme_v013588312.py --query "スファレライトの化学組成は？"
```

Expected: invitation can select an explicit relevant reply; an activity hobby does not answer what one is doing NOW; an unmatched factual query returns UNLEARNED **in this standalone example candidate set**, not in the full Semantic Memory system. Production factual answering should still prioritize verified Semantic Memory.

Limitations: handwritten Japanese patterns for only the development examples, conservative persona screening, no true semantic similarity model yet, no independent evaluation, no model training, no GUI or chat.py integration. Treat these as tests of a selection architecture, not proof of language understanding. Further work: structured theme/role extraction or LLM_SEM model-backed relation scoring and independent evaluation, keeping explicit abstention.
