# v0.13.58.82.41 — /good confirmation for evidence repair

The user no longer needs to copy a Repair ID. After an evidence-conditioned candidate is rejected, the GUI shows the **external unverified reference excerpt**, not the rejected text, and offers the next-turn `/good` command.

- Only `/good` immediately after the displayed evidence answer approves the latest staged Repair ID.
- `/good` automatically proposes the saved external excerpt as the corrected answer, approves it for experimental training, issues `/teachq TOPIC => ANSWER`, then waits for the CLI's explicit teaching success marker before sending `/train`. Training is automatic once the confirmation is given.
- Any other next GUI input **cancels** the pending repair by marking it REJECTED. No training occurs for that repair.
- No repair ID is required and `/repair approve ID` no longer enables training.
- `/good` without a pending rejected-evidence reply does not forward to the CLI or train anything. Existing CLI /good still exists when using chat.py directly; this change is specific to chat_gui.py.
- The model's rejected candidate is never used as the correct answer.
- The reference is external and not independently verified. `/good` serves as the operator's explicit endorsement. This scheme does not implement automatic correctness verification, quality gating of the checkpoint, or holdout regression prior to loading the trained checkpoint.
- The learned question is currently the topic key (e.g. 宇宙), not necessarily the original follow-up wording; this is a known limitation.
- Any other pending trusted learning pairs may be consumed by existing /train.

## PowerShell
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.41-good-repair-confirmation
python -m unittest -v test_good_repair_confirmation_v013588241.py test_rejected_answer_repair_v013588239.py test_auto_repair_training_v013588240.py
python chat_gui.py
```

GUI example:
1. 宇宙とは
2. CPU
3. 宇宙の話に戻って
4. もう少し詳しく
5. Read the Wikipedia fallback; if it is sufficiently correct and you want to train it, enter **/good** as the *very next input*. Otherwise type any other message and the repair candidate will be discarded.

Look for `[Repair Staged]`, `[explicit manual learning pair saved; ...]`, `[Auto Repair Training Started]`, and `[reloaded trained checkpoint: ...]` in diagnostics.
