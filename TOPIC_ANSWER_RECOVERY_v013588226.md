# LLM_CHA v0.13.58.82.26 — Topic Answer Recovery

## Scope
GUI-side bounded answer history (last 12 distinct topics) captures the user's topic question, the original CLI LLM answer and origin label. It is *session-only*. This feature is separate from the user Episode store, trusted Semantic Memory, LLM weights, and Wikipedia Evidence. Recording an LLM answer does **not** verify it.

On `宇宙の話に戻って`, restore the prior `宇宙` answer context and show an explicit historical-answer excerpt. On `もう少し詳しく`, ground the reply in that recovered topic and excerpt; ask what aspect to expand rather than forwarding an underspecified question to the raw generator. A nonexisting topic must never trigger an ungrounded Wikipedia fallback. Replies identified as "未学習" or malformed are not recorded.

## Known limitations
- Current restoration works on answers emitted via CLI `chat.py`; other GUI shortcuts are not comprehensively recorded.
- Wikipedia auto-fallback is recorded only if its status is explicitly successful; a result shape with a different status may not be retained.
- "もう少し詳しく" currently quotes prior content and asks for a specific perspective, rather than producing a newly evidence-verified long explanation.
- No persistence of topic-answer history across GUI restarts.
- Generation-quality filtering is limited to recognized bad answers; this is not a comprehensive factuality classifier.

## Windows verification
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.26-topic-answer-recovery
python -m unittest -v test_topic_answer_context_v013588226.py
python chat_gui.py
```
Try `宇宙とは`, `CPU`, `宇宙の話に戻って`, `もう少し詳しく`, `量子力学とは`. Check that the return and elaboration do not yield "未学習" or "無用反面、知能。".
