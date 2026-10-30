# v0.13.58.82.42 — Per-answer LLM disposition labels

GUI response surfaces now display whether an evidence-conditioned LLM candidate was rejected or passed the Evidence Gate. The status appears immediately beneath each response:

- `［LLM回答：破棄／Evidence Gate: REJECT_NOT_ENTAILED。表示文は参考資料・代替回答］`
- `［LLM回答：採用／Evidence Gate: ...］`
- `［LLM回答：採用せず／未学習判定。参考資料を検索］`
- `［LLM生成：なし／Wikipedia検索結果（外部未検証）］`
- `［LLM生成：なし／参考資料または代替回答］`
- `［LLM回答：採否未判定／CLIの生成・検索ルートをGUIで識別できません］`

Important: Normal chat.py answers can come from corpus-memory retrieval, canonical lookup, or generated responses; the GUI cannot presently identify this from the plain AI> line, so it **does not claim they are accepted LLM-generated answers**. The evidence-conditioned path does have a gate result and is labeled accurately. Future versions can transmit a structured answer provenance record from the CLI to provide a precise label for every answer.

The existing `/good` confirmation and automatic training behavior remain unchanged. Rejecting a candidate is not the same as rejecting the displayed Wikipedia fallback.

## Windows verification

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.42-answer-disposition
python -m unittest -v test_answer_disposition_v013588242.py test_good_repair_confirmation_v013588241.py
python chat_gui.py
```

Try `宇宙とは`, `CPU`, `宇宙の話に戻って`, `もう少し詳しく` and inspect status lines beneath each response. No Windows integration test has yet been run by the assistant.
