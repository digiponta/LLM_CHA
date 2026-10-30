# v0.13.58.82.40 — Auto training after explicit repair approval

The request to enable **automatic learning** is implemented as an automatic `/teachq` → `/train` chain triggered when an operator explicitly approves a repaired answer.

- The model's original rejected text is NEVER trained.
- A retrieved Wikipedia excerpt is still EXTERNAL_UNVERIFIED and NEVER treated as a gold answer automatically.
- The GUI sends `/teachq QUESTION => PROPOSED_ANSWER` after `/repair propose UUID ...` and `/repair approve UUID`. It waits for the CLI's `[explicit manual learning pair saved; ...]` acknowledgement before invoking `/train` automatically.
- `[teaching rejected: ...]` prevents training.
- `[reloaded trained checkpoint: ...]` marks `TRAINED`, confirming reload, **not** validation of learning quality.
- Only one repair can be trained at a time. Progress lives in local `data/rejected_answer_repairs.jsonl`.

## Run on Windows

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.40-auto-approved-repair-training
python -m unittest -v test_auto_repair_training_v013588240.py test_rejected_answer_repair_v013588239.py
python chat_gui.py
```

In GUI: `/repair list`, then `/repair propose UUID 正解文`, then `/repair approve UUID`. The model is trained without issuing a further `/train` manually.

Important: this uses the existing `/train` command, which may consume OTHER pending trusted learning pairs as well. This is **not** a sandboxed, single-example fine-tune; the existing train process determines checkpoint output and any protections. Check existing regression tests before promoting results, and keep backups. No independent holdout comparison is yet wired to automatic promotion. If teaching is rejected or training fails, review the CLI diagnostic output before retrying.

Known limitations: current repair record stores the resolved topic key ("宇宙") rather than the user's full phrasing ("もう少し詳しく"). Status auto-tracking is best effort across process exits; an unclean shutdown can leave TEACH_REQUESTED or TRAIN_REQUESTED. An approval recorded when a training session is busy or chat.py is stopped will not be automatically retried. The stage and approval changes are deliberately separate from external-evidence truth verification.
