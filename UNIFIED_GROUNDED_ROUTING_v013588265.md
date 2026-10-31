# LLM_CHA v0.13.58.82.65 — Unified Grounded Conversation Routing

The regular input in both chat.py and chat_gui.py now tries saved-source grounding for recognizable factual questions (definition, composition, event time, cause) BEFORE the older model/unknown route. Explicit /grounded remains available.

New module chat_unified_grounding_v013588265.py limits this path to short, explicit factual questions and rejects commands/social messages. For a unique matching source in the existing saved Wikipedia snapshot, it calls chat_grounded_bridge_v013588264.py and shows either source-extract with citations and UNVERIFIED / PENDING HUMAN REVIEW indication, or a visible abstention for a sense mismatch. Unrelated subjects, absent snapshots and invalid data keep the old chat route. No new web/network requests; no silent training, approvals, or persistent writes.

**Caution:** This is experimental local snapshot routing, not automatic global trustworthy web retrieval. The 8 existing documents are truncated and unreviewed. An accepted exact quote is not proof that its meaning is right. In particular Universe vs outer space is conservatively abstained; real held-out metrics are not available.

PowerShell:
    cd C:\Users\inoma\git\misc\LLM_CHA
    git fetch origin
    git switch v0.13.58.82.65-unified-grounded-routing
    python -m unittest -v test_chat_unified_grounding_v013588265.py test_chat_grounded_bridge_v013588264.py test_dynamic_definition_v013588263.py
    python chat.py

For GUI open a second terminal and run:
    python chat_gui.py

Try: スファレライトの化学組成は / 水の化学組成は / 量子力学とは / 宇宙とは
Then try: 宝石としてスファレライトが好きです / 銀河の化学組成は
Expected: first factual cases use AUTO_GROUNDED_SNAPSHOT; Universe abstains on sense ambiguity; social and unmatched topics retain the legacy path.

Production checkpoint and /good negative-only training policy remain unchanged.
