# LLM_CHA v0.13.58.82.64 — CLI/GUI Explicit Grounded Answer

Both chat.py and chat_gui.py now recognize the explicit command /grounded QUESTION. Normal chat routing, persona behavior, model inference, Wiki retrieval, /good prohibition and negative signal policy are unchanged.

Shared bridge chat_grounded_bridge_v013588264.py reads the saved v0.60 Wikipedia 8-article JSON file at data/wiki_evidence_review_v013588260.json, matches a unique source by title/aliases, invokes the v0.63 extractor, and displays exact source sentences marked external unverified, human review pending. It does not do live network retrieval or change any training, approval or review files. Simple universe/outer-space sense mismatch is conservatively abstained.

Commands in Windows PowerShell:

    cd C:\Users\inoma\git\misc\LLM_CHA
    git fetch origin
    git switch v0.13.58.82.64-chat-grounded-integration
    python -m unittest -v test_chat_grounded_bridge_v013588264.py test_dynamic_definition_v013588263.py
    python chat.py
    /grounded スファレライトの化学組成は
    /grounded 宇宙とは

Launch python chat_gui.py separately; type the same /grounded commands in its input field. The GUI handles the command locally, without sending it to the child CLI process. The CLI intercepts it before its LLM routes. This feature is opt-in and experimental. Source-exact extraction does not guarantee correctness; independent holdout is not approved.
