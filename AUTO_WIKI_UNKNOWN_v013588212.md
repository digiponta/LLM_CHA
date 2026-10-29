# LLM_CHA v0.13.58.82.12 — Automatic Wikipedia Fallback

Changes (GUI):
- Removes **Wiki検索** button.
- When existing CLI inference returns exactly 「未学習です」, automatically requests Japanese Wikipedia's search/extract API in a background thread.
- Displays up to three relevant excerpts and corresponding Wikipedia article links in the **conversation** tab, explicitly labeled unverified external information.
- If no relevant hits are found, displays 「未学習です（Wikipediaにも該当する検索結果がありません）」.
- A network failure/timeout is **not** represented as no hit: displays a connection error and says unknown status could not be checked.
- LLM answers that are not unknown, existing Evidence answers, causality answers and social/preference responses remain unchanged.
- Previous free-text 「XをWikiで調べて」 command still works; only the dedicated button is removed.
- Auto results are not added to permanent Semantic Memory or learned into the model. They are displayed as external snippets, not generated synthesized answers.

## Windows verification
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.12-auto-wiki-unknown
python -m unittest -v test_auto_wiki_unknown_v013588212.py test_unified_dialogue_context_v013588211.py test_preference_dialogue_v013588210.py
python chat_gui.py
```

## Manual test
1. Ask an unknown factual query such as 「量子力学とは？」. If the existing LLM returns 「未学習です」, GUI should automatically show Wikipedia excerpts and URLs without another button press.
2. Ask nonsense term not on Wikipedia; expect 「未学習です」, not fabricated facts.
3. With internet disabled, expect search connection failure, not a false no-hit claim.
4. Check the GUI has no Wiki検索 button and retains ググる / クリップ読込.
5. Check that 「あなたは誰？」 still goes through ordinary LLM.
6. Test consecutive quick questions carefully: the GUI correlates output and user input in input order. Full concurrent multi-turn requests are not yet supported by the legacy single-threaded chat.py session.

Scope: current implementation is GUI automatic fallback; CLI chat.py does not yet include this auto-search. Wikipedia search result relevance is a conservative keyword check; not independent truth verification.
