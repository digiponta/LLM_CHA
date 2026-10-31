# v0.13.58.82.66 — Answer one sense, display an explicit caution

Behavior for **宇宙とは**:
- If the saved source explicitly defines universe as the totality of things/events, answer that sense first.
- If only an outer-space definition occurs in the saved source, report **that** sense, explicitly warning that the universe sense has not been established in the excerpt. Never assert an unsupported universe definition.
- For **宇宙空間とは**, answer the outer-space sense when explicitly grounded.
- Display a source-exact evidence sentence, source URL, and external-unverified / human-review-pending warning.
- If neither meaning is source-grounded, retain conservative abstention.

The shared bridge chat_grounded_bridge_v013588264.py is updated; both chat.py and chat_gui.py automatically inherit this behavior through existing v0.65 routing. No changes to model weights, saved evidence, approval, /good policy or production training.

PowerShell:

    cd C:\Users\inoma\git\misc\LLM_CHA
    git fetch origin
    git switch v0.13.58.82.66-sense-notice
    python -m unittest -v test_universe_sense_notice_v013588266.py test_chat_grounded_bridge_v013588264.py test_chat_unified_grounding_v013588265.py
    python chat_gui.py

Try 宇宙とは and 宇宙空間とは, both with and without /grounded.

These are deterministic lexically grounded senses, not a trained semantic disambiguator and not independent factual verification.
