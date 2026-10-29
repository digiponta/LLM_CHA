# v0.13.58.82.7 — Extractive General Evidence Retrieval (experimental)

## Scope
The GUI performs conservative, in-memory retrieval for short menu/food questions. It supplements the existing v0.13.58.82.5 labeled-attribute extraction. It **does not** infer or invent products; it displays brief matching source lines as unverified quotations.

- Search without clipboard/Wikipedia text: reports that no temporary evidence has been loaded, rather than "未学習です".
- Evidence with matching, explicitly labeled menu/food lines: shows verbatim excerpts and the "外部未検証" source.
- Evidence with no relevant statement: reports evidence insufficiency.
- Topic switches isolate the old topic's evidence.
- Existing LLM_TRY, /sleep, model checkpoints, and Semantic Memory remain untouched.
- The general retrieval is GUI-only at this stage. It is intentionally limited: arbitrary web text, HTML menus and implicit descriptions may not be recognized.

## Windows run
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.7-general-evidence-retrieval
python -m unittest -v test_general_evidence_retrieval_v01358827.py test_evidence_provenance_v01358826.py test_evidence_attributes_v01358825.py
python chat_gui.py
```

## Manual protocol
1. 「スターバックスをぐぐって」
2. 「メニューは？」 — should request clipboard because Google only opens a browser.
3. Copy a text excerpt explicitly containing menu or food categories and the topic.
4. 「クリップ読込」.
5. 「フードの種類は？」 — displays relevant verbatim lines, or a clear "no relevant source statement" message.
6. 「スファレライトをぐぐって」 and ask "メニューは？" — should not reuse the Starbucks evidence.

This is **evidence retrieval**, not factual verification. Relevance and conflict-aware verification are planned later.
