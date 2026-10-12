# LLM_CHA v0.2.33.82.4 — Opt-in chat.py Truth-Gate Integration

`chat.py` now loads the context adapter **only** if `LLM_CHA_MULTITOPIC=1`.
Default remains unchanged. Topic resolution runs only after existing command
handling, before retrieval-first, semantic knowledge resolution, and Truth Gate.
The routing result is a query, never a knowledge assertion.

```powershell
git pull origin v0.2.33.82-multitopic-context
python -m unittest -v test_multi_topic_context_v0233821.py test_conversation_topic_adapter_v0233822.py test_multi_topic_chat_runtime_v0233823.py test_truth_aware_chat_integration_v0233824.py
$env:LLM_CHA_MULTITOPIC="1"
python chat.py
```

Trial inputs: `宇宙について教えて`, `GPUとは`, `宇宙の話に戻って`,
`もう少し詳しく`, `それについて`, `/reset`, `もう少し詳しく`.

Disable with `Remove-Item Env:LLM_CHA_MULTITOPIC`.

**Important:** The unit tests for this version verify source placement and
adapter behavior. They do NOT establish correctness of real model response,
GPU execution, or the old 5/5 acceptance regression. Test with the intended
checkpoint and inspect Truth Gate output before interpreting as end-to-end PASS.

Note: This is an experimental narrow extraction of explicit topic phrases;
free-form implicit topic shifting is not yet generalized.
