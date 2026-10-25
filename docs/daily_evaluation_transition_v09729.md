# LLM_CHA v0.9.7.29 — Intent-Driven Early Evaluation Transition

This is a **runtime routing** fix for the observed failure:
`黒耳を飲んだ → 満足した` previously fell through to the low-confidence
LLM path and was rejected as 未学習です.

Explicit short assessments are now recognized while a clipboard product
experience is active, **without requiring two taste turns**:
- POSITIVE: 満足した → それは良かったね。
- DISAPPOINTMENT: 期待外れだった → それは残念だったね。
- SADNESS: 悲しかった → それは悲しかったね。

This assessment closes the product dialogue and writes the transient
Semantic State evaluation with USER_REPORTED provenance and an emotion label.
Existing two-taste closure remains backward compatible (it still returns
the previous 「満足できたのね」 response). A question ending in ？ or ?,
an unrelated topic or a new clipboard load must not be treated as an
experience conclusion.

This branch adds a conservative deterministic response strategy, **not
GPU SFT**. The 30 training / 12 holdout dataset from v0.9.7.28 remains
available for a separate checkpoint experiment later. Neither model weights
nor persisted Semantic Memory are modified.

## Windows PowerShell
```powershell
git fetch origin
git switch --track origin/v0.9.7.29
python -m unittest -v test_daily_evaluation_transition_v09729.py test_clipboard_conclusion_v09719.py test_conversation_semantic_state_v09721.py
python chat.py
```

With the Starbucks menu copied:
```text
/read-clipboard
黒耳を飲んだ
満足した
/conversation-semantic-status
```

Expected: `それは良かったね。` and semantic state `CLOSED`
with evaluation emotion `POSITIVE`, not `未学習です`.
