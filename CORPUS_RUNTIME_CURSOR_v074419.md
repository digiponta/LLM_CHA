# v0.7.44.19 — Evidence Cursor Runtime Integration

The `chat.py` corpus-first UNVERIFIED path now initializes an
EvidenceCursor from the original `RetrievalFirstResult.records` via
`bridge_records`. It marks propositions already present in the first
answer as shown. A subsequent immediate `もう少し詳しく` or `もっと詳しく`
offers one genuinely unshown source record, including its provenance
and proposition ID. It never auto-promotes or trains on evidence.

If no unseen record exists, the v0.7.44.15 no-new-evidence reply remains.
Since the corpus retrieval normally joins all statements into its
initial answer, **no additional corpus record is expected in the
typical 宇宙 example**. This is correct rather than a malfunction.

## Verify

```powershell
git pull
python -m unittest -v test_corpus_runtime_cursor_v074419.py test_stable_proposition_id_v074418.py test_corpus_cursor_bridge_v074417.py test_evidence_cursor_v074416.py
python chat_gui_v07447.py
```

Try: 宇宙とは → もう少し詳しく → 量子重ね合わせについて教えて.
`corpus_cursor=status:READY, ... remaining=0` is expected for a
fully displayed corpus answer. Inspect status on CLI because the
GUI normally hides diagnostics.

Integration has not been tested on the user's Windows GPU runtime.
