# LLM_CHA v0.9.7.21 — Conversational Semantic State

This version adds **in-memory, ephemeral** structured observations alongside
the existing ClipboardDialogue. It does not change the existing natural
language answer route or connect the LLM generator yet.

The state schema (`conversational-semantic-state-v0.1`) distinguishes:
- `entity`, with `entity_provenance=CLIPBOARD_UNVERIFIED`
- `event=consumption` or `taste_report`, with `actor=user`
- `attributes` such as acidity, sweetness, chocolate, all individually
  tagged `USER_REPORTED`
- `evaluation` (e.g. 満足した) tagged `USER_REPORTED`
- `status`: EMPTY / ACTIVE / CLOSED

The snapshot is transient, never written to disk, and never eligible for
auto-promotion or training. A new clipboard read clears it; switching to an
unrelated topic while an experience is active clears it as well. A completed
experience can be inspected during the current session.

```powershell
git fetch origin
git switch --track origin/v0.9.7.21
python -m unittest -v test_conversation_semantic_state_v09721.py test_clipboard_product_resolution_v09720.py test_clipboard_conclusion_v09719.py
python chat.py
```

After `/read-clipboard`, use the usual experience sequence:
```text
黒耳を飲んだ
酸味と甘さのバランスが良かった
黒耳は、ブラックチョコレートで甘かった
満足した
/conversation-semantic-status
```

This is a schema and observation experiment, not free-form semantic parsing.
Before injecting it into model prompts, validate privacy, expiry, source
attribution and generated-answer grounding.
