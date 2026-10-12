# LLM_CHA v0.2.33.82.2 — Multi-Topic Runtime Adapter (experimental)

Adds an independent, deterministic adapter around v0.2.33.82.1 topic context.

- Explicit topics, topic return, contextual follow-up
- Conservative ambiguity handling: request clarification instead of guessing
- Exact `/reset` clears transient topics only
- Other slash commands pass unchanged to their original handler
- No Semantic Memory writes, no Truth State writes, no model calls
- `READY` carries a query into the **existing** Truth Gate; it is **not** an accepted answer

## Local verification

```powershell
python -m unittest -v test_multi_topic_context_v0233821.py test_conversation_topic_adapter_v0233822.py
```

## Runtime integration point (requires local runtime files)

```python
from conversation_topic_adapter_v0233822 import ConversationTopicAdapter
adapter = ConversationTopicAdapter()  # once per conversation session

route = adapter.process_user_turn(user_input)
if route.action in ("CLARIFY", "RESET", "NO_TOPIC"):
    print(route.response)
elif route.action == "COMMAND":
    handle_existing_command(user_input)
else:
    # IMPORTANT: only this existing verified pipeline can produce an answer
    answer = existing_truth_aware_runtime(route.rewritten_query)
    print(answer)
```

Do not install this pseudocode literally until adapting to the real runtime interfaces.
The v0.2.33.81 runtime files are not present on the connected GitHub branch.
Integration with that local runtime and GPU regression remain pending.
