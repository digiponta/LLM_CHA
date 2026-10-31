# v0.13.58.82.82 — Conservative Response Quality Guard

The observed bad reply to **今日は何をしてる？** began with `。` and had lexical probe agreement 0.057 versus threshold 0.35, but semantic rescue accepted it. This release rejects **only the conjunction of a clearly malformed leading punctuation token and low lexical probe agreement**; low agreement alone does not trigger rejection.

The quality check executes inside the normal `chat.py` answer path, immediately before `classify_resolution`, so a rejected answer is not silently treated as KNOWN or entered into accepted-turn history.

The existing `UNKNOWN_REPLY` path is used instead. This is not yet a general dialogue quality metric and does not ensure a natural answer.

Windows:

    cd C:\Users\inoma\git\misc\LLM_CHA
    git fetch origin
    git switch v0.13.58.82.82-response-quality-guard
    python -m unittest -v test_response_quality_guard_v013588282.py test_chat_semantic_paraphrase_v013588281.py test_chat_semantic_retrieval_v013588280.py
    python chat.py

Ask `今日は何をしてる？` several times. Sampling may produce different generations; note raw candidate and quality reason. Also test `閃亜鉛鉱について教えて` to ensure registered retrieval has not regressed.

This is a targeted quality guard, not proof that the LLM has learned natural conversation.
