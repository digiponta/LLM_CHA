# v0.13.58.82.80 — Minimal Chat Semantic Memory Retrieval

The registered-memory probe is now connected to the CLI chat.py **only for three exact test questions**, before automatic Wikipedia snapshot grounding. This is intentionally narrow to demonstrate runtime value without building more approval infrastructure.

Test:
    git fetch origin
    git switch v0.13.58.82.80-chat-semantic-retrieval
    python -m unittest -v test_chat_semantic_retrieval_v013588280.py test_sense_retrieval_probe_v013588279.py
    python chat.py

Then ask:
- 閃亜鉛鉱とは？
- スファレライトとは？
- 閃亜鉛鉱の化学組成は？

Expected: MEMORY_ATOMIC_EXACT, MEMORY_EVIDENCE_ALIAS, MEMORY_ATTRIBUTE_NOT_EXPLICIT. Compare actual chat logs with probe results. The formula is intentionally not inferred because ZnS has not been registered explicitly. Other questions follow the unchanged chat flow.

This is NOT a broad semantic retrieval system. Does not modify model weights, GUI, records or existing review gates. A missing or unreadable memory source causes an explicit diagnostic response. The source remains external and unverified.
