# LLM_CHA v0.2.33.81 — Context Persistence & Evaluation Compatibility

Two reports from v0.2.33.80 showed **8/8 exploratory turns executed**, and reference, thanks, follow-up safety improved. The extended acceptance result fell to **4/5** only because the new legitimate `speech-act=REFERENCE_CLARIFY` log did not match an old `multi-intent=REFERENCE_CLARIFY` expression.

Changes:
1. The fifth extended benchmark case now accepts either valid reference marker while preserving its answer assertion.
2. A small explicit-topic tracker remembers topics in patterns like `宇宙について教えて` and `GPUとは`.
3. `もう少し詳しく` with an explicit remembered topic becomes `Xとは`, **re-entering existing semantic/Truth-Aware dispatch** rather than answering by free generation. Without a recorded topic, the existing clarification remains.
4. No verification or Truth State is inferred from context, and no model weights are updated.

Limitations: topic extraction is pattern-based and deliberately narrow. It can carry a previously mentioned topic through later turns, so it is not general conversational coreference. This is a proof-of-mechanism for explicit topic state, not proof that richer follow-up prompts are semantically solved.

Windows PowerShell:

```powershell
git fetch origin
git switch v0.2.33.81
git pull origin v0.2.33.81
python -m py_compile chat.py speech_act_reference_v023380.py extended_chat_runtime_v023378.py
python -m unittest -v test_context_topic_v023381.py test_speech_act_reference_v023380.py test_extended_chat_runtime_v023378.py
python extended_chat_runtime_v023378.py --run --timeout 240
python conversation_generalization_v023379.py --run --timeout 240
```

Expected: the extended reference-variant checks the new marker successfully, while the follow-up `宇宙について教えて` → `もう少し詳しく` uses `FOLLOWUP_TOPIC_ROUTE` and still receives a Truth-Aware `UNVERIFIED` block for `宇宙`. These outcomes are **not verified on the user's machine yet**.
