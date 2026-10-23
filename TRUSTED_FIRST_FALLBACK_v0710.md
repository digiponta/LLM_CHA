# LLM_CHA v0.7.10 — Trusted-first UNKNOWN Fallback

Policy:
1. Query **Approved Memory** first. Exact approved QA matches return immediately.
2. If no approved answer exists, return `UNKNOWN`.
3. **Only when explicitly opted in**, ask the Experimental Adapter.
4. Label experimental responses `EXPERIMENTAL_UNVERIFIED` / 未承認.
5. Never promote Candidate knowledge or change Trusted weights automatically.

This is a **standalone pilot**. The production `chat.py` has its own
Semantic Memory and Truth Gate. **Not all unknown responses from an LLM
can be reliably inferred by inspecting its text**; a structured UNKNOWN
result is mandatory for the router. This pilot uses exact Approved Memory
lookups as its trusted authority, not the entire trusted LLM routing stack.
The experimental model may still hallucinate; its answers are for review.

## Windows

```powershell
git fetch origin
git switch --track origin/v0.7.10
python -m unittest -v test_trusted_first_router_v0710.py test_multi_knowledge_v079.py
```

Default, trusted-only pilot:
```powershell
python chat_trusted_first_v0710.py
```

Explicitly allow unverified fallback:
```powershell
python chat_trusted_first_v0710.py --allow-experimental
```

A missing Approved QA is treated as UNKNOWN in this pilot. When a trusted
answer exists, the Experimental Adapter is **never queried**, even with
`--allow-experimental`.

Next: integrate a structured UNKNOWN signal from production `chat.py`
Truth Gate while keeping existing Wikipedia evidence and conversation
context behavior intact. Do not route every uncertain free-generation
answer into the candidate model.
