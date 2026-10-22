# LLM_CHA v0.6.36 — Opt-in approved QA in real chat.py

This branch connects v0.6.35's approved exact-question JSONL overlay into
the interactive `chat.py` loop **before model generation**.
It is disabled by default, **read-only**, and never intercepts slash commands.
Unapproved rows are ignored; conflicting approved answers raise an error.
On each match the runtime prints the answer and a provenance route.

This is an experimental exact-match retrieval path only. It is not yet the
canonical Semantic Memory data store, not multi-turn/semantic paraphrase search,
and not an automated `/sleep` trainer.

## PowerShell
```powershell
git fetch origin
git switch --track origin/v0.6.36
python -m unittest -v test_chat_approved_overlay_v0636.py test_memory_first_v0635.py

python chat.py `
  --approved-qa-overlay data/semantic_memory_first_v0635.example.jsonl
```

Type `v0632実験の合言葉は何ですか`. Expected:
```
AI> 検証専用の合言葉です。
[route=APPROVED_QA_OVERLAY, source_id=qa-v0632-manual-test, model_weights_unchanged=True]
```

Then type `こんばんは` and `猫`; these are not in the overlay and continue
to the existing chat pipeline. Use `/exit` to stop.

To test opt-out, use `python chat.py` without the flag. No overlay
will be loaded. Note: without the flag the existing chat runtime retains
all of its previous behavior. To preserve context, the current overlay does not
record hits as accepted dialogue turns; conversational memory integration is
future work.

Do not place unreviewed or user-private data in the committed example file.
In production use separate reviewed stores and explicit audit policies.
