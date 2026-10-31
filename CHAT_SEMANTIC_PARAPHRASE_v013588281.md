# v0.13.58.82.81 — Small-step Semantic Memory Paraphrase Routing

This update extends the narrow registered-memory route from v0.80 to a small explicit set of Japanese paraphrases. No new approval process, knowledge import, checkpoint training, or GUI integration. The previously wired chat.py continues to call the same `chat_semantic_retrieval_v013588280.route`.

Supported examples:
- 閃亜鉛鉱とは？ / 閃亜鉛鉱について教えて / 閃亜鉛鉱って何？
- スファレライトとは？ / スファレライトって何？ / スファレライトについて教えて
- 閃亜鉛鉱の化学組成は？ / スファレライトの化学式は？

Only definition and provenance-supported alias retrieval are answered. Formula requests still abstain when the registered proposition lacks an explicit chemical formula. Unrelated questions pass through the previous chat routing.

Windows:

    cd C:\Users\inoma\git\misc\LLM_CHA
    git fetch origin
    git switch v0.13.58.82.81-semantic-paraphrase-routing
    python -m unittest -v test_chat_semantic_paraphrase_v013588281.py test_chat_semantic_retrieval_v013588280.py
    python chat.py

Ask the paraphrases above and compare routes. This is intentionally a bounded experiment rather than a general semantic search implementation.
