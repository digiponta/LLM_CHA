# v0.13.58.82.36 — Evidence-Aware Candidate Routing

The prior GUI test passed the input protocol but returned REJECT_UNKNOWN, indicating the normal `chat.py` selective/Unknown path rejected an evidence-heavy user turn.

This experiment adds an explicit one-line `/evidence-candidate <URL-safe-base64 JSON>` request to chat.py. It decodes a bounded topic and retrieved excerpt, constructs an isolated generation prompt, and runs existing `generate_reply` with a deterministic greedy candidate. Only this candidate-only route bypasses the *ordinary* Unknown Gate. It does not append accepted dialog history, enqueue teaching data, promote external evidence, invoke /sleep, or change normal questions.

The GUI wraps its already-retrieved external evidence in the command and still runs the preexisting independent `final_answer` evidence gate against any generated candidate; an unsupported candidate falls back to the attributed excerpt. Thus bypassing the ordinary Unknown Gate does **not** mean trusted or approved output. This is a research experiment and not proof of entailment or factual correctness.

## Windows

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.36-evidence-aware-route
python -m unittest -v test_evidence_aware_route_v013588236.py test_response_correlation_v013588235.py test_prompt_normalization_v013588234.py
python chat_gui.py
```

Conversation: `宇宙とは`, `CPU`, `宇宙の話に戻って`, `もう少し詳しく`, `/genstats`. Inspect `[Evidence-Aware Candidate Route]` and `[Evidence Gate]` diagnostics; a non-unknown result may still be REJECT_NOT_ENTAILED. This branch has not been run on the user's local GPU.
