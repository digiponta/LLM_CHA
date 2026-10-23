# v0.7.44.20 — Wikipedia topic context after alias normalization

Bug reproduced by conversation:
- 量子ビットとは？ → Wikipedia topic 量子ビット active
- 量子重ね合わせについて教えて → normalized Wikipedia lookup succeeded
- もっと詳しく ×3 → old 量子ビット details, not 重ね合わせ

Root cause: the v0.7.44.14 alias early-return printed Wikipedia
answer but did not call `cha_wiki_conversation.offer(wiki_context)`.
The existing follow-up system therefore still had the previous topic.

The successful alias branch now offers the actual normalized Wikipedia
context before showing its answer. It requires `wiki_context` and
does not alter truth labels or auto-promote evidence.

```powershell
git pull
python -m unittest -v test_alias_topic_followup_v074420.py test_topic_normalization_runtime_v074414.py
python chat_gui_v07447.py
```

Manual check:
1. 量子ビットとは？
2. 量子重ね合わせについて教えて
3. もっと詳しく
4. もっと詳しく
5. CPUとは

Expected: (3)-(4) remain within 重ね合わせ evidence or return an
evidence-insufficient message; never switch back to 量子ビット.
GPU/UI acceptance remains to be performed locally.
