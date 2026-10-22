# LLM_CHA v0.6.9 — Aozora Literature Semantic Router (opt-in)

This is a **conservative pilot** connecting literature lookups to the
v0.6.4 Aozora JSONL corpus. The router checks text hashes and authored
provenance (author/title), and emits the existing natural-language reference.
It does not modify checkpoints, trust state, Semantic Memory or /sleep.

PowerShell:

```powershell
git fetch origin
git switch --track origin/v0.6.9
python -m unittest -v test_aozora_literature_router_v069.py test_chat_window_v061.py
$env:LLM_CHA_AOZORA_ROUTER="1"
python chat_window_v061.py --latest-experimental
```

Try: `吾輩`, `吾輩は猫であるについて`, `猫は`, `長門`, `宇宙`.
The router recognizes only explicitly enumerated titles and a short alias.
`猫は` asks for clarification instead of inventing an interpretation.

Output is a book identification and follow-up question, *not* a generated
literary summary. The first source text URI and official card URL are
printed in diagnostic metadata; raw prose is not yet extracted for a user
question. This feature is opt-in because routing precedence and multi-turn
interactions have not passed full regression. It does not change /sleep or
unknown-teaching behavior.

To disable:

```powershell
Remove-Item Env:LLM_CHA_AOZORA_ROUTER
```

Limitations: only curated works 789/1567 and direct string-title triggers,
no large-scale vector retrieval, author disambiguation, passage citation
selection, persistent session topics or SKI transfer. Any use of title
matching must not be mistaken for learned weights or a verified fact.
