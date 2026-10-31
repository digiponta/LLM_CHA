# LLM_CHA v0.13.58.82.79 — Retrieval Smoke Test

This is deliberately small. It performs three read-only questions against the user's **already registered** 閃亜鉛鉱 knowledge: exact subject, evidence-supported synonym スファレライト, and a missing explicit chemical formula question. It validates corresponding Atomic Proposition, Unified Memory and provenance entries. It does **not** yet integrate into chat.py's routing and does not generate text with the model. The observed route/answer from this script must not be presented as proof that chat.py successfully used the knowledge.

Windows:

    cd C:\Users\inoma\git\misc\LLM_CHA
    git fetch origin
    git switch v0.13.58.82.79-semantic-retrieval-probe
    python -m unittest -v test_sense_retrieval_probe_v013588279.py
    python sense_retrieval_probe_v013588279.py

Next run the same three questions in chat.py or the GUI and compare actual results. Any mismatch indicates a runtime routing/integration issue that should be fixed before adding more governance machinery.

The alias is supported only when the original source evidence explicitly contains スファレライト. The registered proposition does not explicitly encode ZnS; the probe abstains instead of inventing a formula. Knowledge sources remain externally unverified and this is a smoke diagnostic.
