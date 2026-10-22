# LLM_CHA v0.6.40 — Explicit cross-session topic persistence

The session-local multi-topic Wikipedia context can now be saved and loaded
as versioned JSON. The file is `data/topic_context_v0640.json` on the local
machine. The saved context includes the ordered list of up to four topics,
each topic's extract, evidence URL and `EXTERNAL_UNVERIFIED` truth state,
plus the active topic. No model or production Semantic Memory is modified.

## Commands
- `/context-save`: atomically save the current topics and selected topic.
- `/context-load`: validate the saved JSON completely before replacing the
  current session context. On error, the current in-memory context stays intact.
- `/context-clear`: clear *session-only* topic context; saved file unchanged.
- `/exit`: end session; context is not saved automatically.

## Run on Windows

```powershell
git fetch origin
git switch --track origin/v0.6.40
python -m unittest -v test_persistent_topic_context_v0640.py test_multi_topic_evidence_v0639.py

python chat.py --approved-qa-overlay data/my_approved_qa_test.jsonl
```

In chat session A:
```text
スターバックスとは
トヨタの話題
スターバックスに戻って
/context-save
/exit
```

Restart `chat.py` and enter:
```text
/context-load
メニューは
トヨタに戻って
所在地は
/context-clear
```

Saved files may contain personal topics or URLs. Keep them local and
exclude them from version control if needed. Invalid schema, out-of-bounds
topic counts, duplicates, invalid active references, and forged truth states
are rejected. Automatic expiry and cross-machine synchronization are not
implemented; no external information is promoted by loading.
