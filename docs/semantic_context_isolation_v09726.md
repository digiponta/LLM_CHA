# LLM_CHA v0.9.7.26 — Semantic Context Failure Isolation

Controlled real-checkpoint diagnostic for the previously failing semantic
context prefix. Seven cases share exactly the same identity question:

A. no prefix
B. 「商品を飲んだ。」
C. 「フラペチーノを飲んだ。」
D. 「黒耳を飲んだ。」
E. full product name and experience sentence
F. 「会話対象: 黒耳。体験: 飲んだ。」
G. forced two-turn dialogue: 「こんにちは」→「こんにちは。」 then identity question

Unlike v0.9.7.25, G does **not** pass through the history relevance
selector: its actual prompt is directly constructed and reported.
A-F use the same canonical runtime prompt constructor.

The report contains full prompts, prompt token counts, generation results,
confidence, and exact identity answer matching. Fixed parameters:
temperature 0, top_k 3, seed 42, repetition penalty 1.08, max 64 tokens.

These are controlled diagnostic cases, not an independent held-out
benchmark. Because prompt wording and length co-vary in B-F, a failed
case identifies a suspect expression, not a proven causal token. Further
matched-length controls may be needed.

No model training, auto promotion, or automatic answer selection is done.

## Windows PowerShell
```powershell
git fetch origin
git switch --track origin/v0.9.7.26
python -m unittest -v test_semantic_context_isolation_v09726.py test_context_robustness_diagnostics_v09725.py
python chat.py
```

At the CLI:
```text
/semantic-context-isolation-audit
```

Review the first case that deteriorates (B-F) and G's forced history
behavior. In particular, compare G against A to assess true multi-turn
continuation rather than the pruned history in v0.9.7.25.
