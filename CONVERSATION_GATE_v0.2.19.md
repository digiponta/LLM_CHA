# v0.2.19 — Conservative Conversation Gate and Followup Context

This version changes only conversation runtime behavior; **no model weights are trained**.

- `conversation_gate_v0219.py`: selectively restore a semantically coherent candidate rejected for low lexical probe agreement. Eligibility: genuine small talk (not factual/definition queries), semantic validation passed, slots covered, confidence >= .45, minimum token confidence >= .05, mean margin >= .05, semantic probe agreement >= .90, sufficient text and no obvious generic/quality problem. The rescue is not applied to internalized/verified memory, truth-state warnings, question repetition, or failed context quality checks.
- `topic_followup`: prepend only prior **user-authored** topical text for short references such as `その話` or `それ`, when normal pending-prefix logic did not already retain it. Never interpolate a rejected AI answer into history.
- `chat.py`: integrates both interventions before output/routing. Knowledge state RAW_CORPUS_ONLY, unknown concepts and truth-state restrictions remain under original protection.

## Run (PowerShell)
```powershell
git fetch origin
git switch --track origin/v0.2.19
python -m unittest -v test_conversation_gate_v0219.py test_dialogue_state_v029.py test_conversation_quality_v027.py
python chat.py --model model/model-llm-cha-foundation-dialogue-v0218.pt --tokenizer ../LLM_TRY/model/tokenizer-v0.7-bpe.json --show-context
```
Try: `こんにちは`, `最近、SF小説を読んでいます`, `その話を続けて`, `長門有希について教えて`.

**Important limitations:** the heuristics are conservative but not proof of safety. True lexical disagreement can reflect semantic contradiction; keep gate review logs and measure accepted wrong replies. The 0.2.18 quality improvements still require independent generation evaluation. The dialogue prefix only works when character-mode chatter is active and dialogue-history turns are enabled. All model checkpoints remain local and unchanged.
