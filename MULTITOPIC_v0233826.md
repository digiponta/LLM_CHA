# LLM_CHA v0.2.33.82.6 — Non-Repetitive Grounded Expansion

Experimental change, enabled only with `LLM_CHA_MULTITOPIC=1`.

## Changes
- Splits a corpus response only at explicit ` / ` separators.
- First query for an extracted topic presents the first proposition, rather than the entire corpus text.
- Each explicit follow-up advances to the next unseen proposition in the same source record.
- Topic switches retain independent cursors; `/reset` clears all cursors.
- Existing Truth Gate controls eligibility. UNVERIFIED content is prefixed
  `【未検証の記録】` rather than presented as verified fact.
- Once all propositions are shown, explicit follow-ups say no unseen
  material remains rather than running unconstrained generation.
- No model retraining or Semantic Memory / Truth State writes.

**Limitation:** Per-proposition Truth State is NOT yet separately stored;
the effective subject Truth State is inherited by each fragment.
The source corpus may mix genuine and speculative statements. These fragments
must not be treated as independently validated facts.

## Local tests
```powershell
git pull origin v0.2.33.82-multitopic-context
python -m unittest -v test_multi_topic_context_v0233821.py test_conversation_topic_adapter_v0233822.py test_multi_topic_chat_runtime_v0233823.py test_truth_aware_chat_integration_v0233824.py test_learning_init_v02338241.py test_grounded_followup_v0233825.py test_grounded_expansion_v0233826.py test_expansion_integration_v0233826.py
```
Expected: **62 tests** (47 existing + 7 cursor + 8 integration).

```powershell
$env:LLM_CHA_MULTITOPIC="1"
python chat.py
```
Try `宇宙について教えて`, `GPUとは`, `宇宙の話に戻って`,
`もう少し詳しく` twice, `/reset`, `もう少し詳しく`, `/exit`.

This is a new behavior: for known corpus topics, the initial response is
deliberately shorter. Verify it does not break other retrieval expectations
on real hardware. PASS is not claimed until local execution.
