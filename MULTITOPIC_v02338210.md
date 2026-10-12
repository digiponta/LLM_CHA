# LLM_CHA v0.2.33.82.10 — GPU chat acceptance (opt-in)

This version provides a scripted smoke test that launches the **real chat.py**
with the user's installed CUDA checkpoint and tokenizer, a temporary copy of
the source Corpus Memory, and a temporary five-state proposition overlay.
Overlay assertions are synthetic *test labels*, not scientific reviews.
The source file is not altered, and no teaching/training commands are sent.

## Run

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git pull origin v0.2.33.82-multitopic-context

python -m unittest -v test_multi_topic_context_v0233821.py test_conversation_topic_adapter_v0233822.py test_multi_topic_chat_runtime_v0233823.py test_truth_aware_chat_integration_v0233824.py test_learning_init_v02338241.py test_grounded_followup_v0233825.py test_grounded_expansion_v0233826.py test_expansion_integration_v0233826.py test_proposition_truth_v0233827.py test_truth_integration_v0233827.py test_proposition_review_v0233828.py test_mixed_state_e2e_v0233829.py test_mixed_state_gpu_accept_v02338210.py

python mixed_state_gpu_accept_v02338210.py --timeout 240
```

Expected unit test count: **94** (90+4), pending Windows runtime verification.

The runner writes `results/mixed_state_gpu_accept_v02338210.json`,
including the full GPU transcript, success/failure results, and exit code.
Please return that JSON result or console summary so failing cases can
be investigated.

## Acceptance limits

- The script uses the actual `宇宙` corpus record and **simulates**
  per-proposition decisions FALSE, TRUE, UNVERIFIED, OUTDATED and CONTESTED.
  These synthetic assignments are not factual endorsements.
- It copies the corpus into a temporary directory and passes
  `--corpus-memory` and `LLM_CHA_PROPOSITION_TRUTH` to the child process.
  Temporary files are discarded when the process exits.
- It does **not** virtualize all other runtime files. chat.py may read or
  initialize its ordinary Semantic Memory, learning-state and other support
  files. Do not treat this as comprehensive process-level isolation; run
  with training disabled and on a checked-out test working copy if full
  data isolation is required.
- It does not require changes to the existing trusted reviews.
- The runner is acceptance infrastructure; it does not establish that the
  model has learned these propositions into its neural weights.
