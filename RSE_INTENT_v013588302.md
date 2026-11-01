# v0.13.58.83.02 — Intent-aware RSE routing

The v0.13.58.83.01 pilot returned NO_CONTENT_TERMS for 最近どう？ and insufficient content coverage for スファレライトとは？; both abstentions were correct for keyword-only retrieval.

This phase adds a **diagnostic-only** intent router. For four common social intents it offers an original, assistant-safe template rather than repeating CP's experiences. Factual questions are deferred to existing Semantic Memory, and all other questions to v0.13.58.83.01 content retrieval. It does not use the 2,286 RealPersonaChat answers for intent ranking yet, and makes **no changes** to chat.py or the model.

Run on Windows:

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.83.02-intent-aware-rse
python -m unittest -v test_rse_intent_v013588302.py test_rse_content_terms_v013588301.py
python rse_intent_router_v013588302.py --question "最近どう？"
python rse_intent_router_v013588302.py --question "少し話さない？"
python rse_intent_router_v013588302.py --question "今何してる？"
python rse_intent_router_v013588302.py --question "スファレライトとは？"
```

Status SAFE_TEMPLATE_CANDIDATE means only a conservative proposed response, NOT a live model response. DEFER_TO_EXISTING_MEMORY and DEFER_TO_CONTENT_RSE are intended routes, not actual calls. Future: add provenance-backed answer candidate retrieval inside each intent, independent relevance assessment, and comparison to baseline on held-out conversational questions before enabling runtime selection or expansion.
