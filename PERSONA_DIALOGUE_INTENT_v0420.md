# LLM_CHA v0.4.20 — Persona Dialogue Intent / Incomplete Input Guard

Addresses observed `貴方は` misrouting into persona-corpus retrieval. The exact fragments `貴方は`, `あなたは`, `あなたの`, `私は`, etc. now return `persona> 続きを聞かせて。` before persona evidence or Truth Gate retrieval. No partial input is silently converted into an identity claim.

A separate read-only classifier labels IDENTITY, INCOMPLETE, KNOWLEDGE, CONVERSATION and OTHER. Only INCOMPLETE is intercepted; all other intents pass through existing processing, including v0.4.19 identity, Wikipedia v0.4.18 and canonical retrieval.

Guardrails: slash commands bypass, topic-bearing questions are not fragments, no memory/training writes, Truth Gate unchanged. Exact-pattern coverage only; this is not full natural-language dialogue understanding.

## Windows verification

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_persona_dialogue_intent_v0420.py test_persona_identity_guard_v0419.py test_article_proposition_alignment_v0418.py
python verify_integration_v0366.py --gpu --legacy --timeout 240
python chat.py
```

Interactive checks: `貴方は`, `あなたの`, `貴方は誰`, `あなたは誰ですか`, `今日は何をしていたの`, `化学とは`, `CPUとは`, `長門`. Observe that exact fragments request clarification while complete and factual questions keep existing routes. No Windows GPU execution has been claimed.
