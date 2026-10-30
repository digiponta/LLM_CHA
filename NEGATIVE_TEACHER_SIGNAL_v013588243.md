# v0.13.58.82.43 — Negative teacher signal for discarded LLM answers

For an evidence-gate rejection, the bad model response is recorded in the repair queue as `rejected_candidate`. When the operator confirms the fallback with `/good`, the approved reference excerpt becomes `answer_candidate`, while the earlier discarded candidate becomes the negative example.

The existing GUI automatically calls `/teachq` and then `/train`. The `online_train.py` trainer now automatically reads `data/rejected_answer_repairs.jsonl` and uses only pairs satisfying all of:
- `approval == EXPLICIT_HUMAN` and `state == APPROVED`;
- explicit recognized rejection gate;
- a distinct nonempty rejected candidate and correct answer;
- the **exact positive question and answer pair is among the current pending trusted pairs**; already-consumed pairs do not automatically repeat negative training.

Loss is positive supervised learning plus a weak negative preference contrast:
`loss = positive_CE + 0.05 * softplus(mean_logp(rejected|question) - mean_logp(correct|question) + 0.2)`.
This discourages the rejected **full sequence relative to the approved positive**. It is *not* a universal prohibition of common tokens like 脳, 宇宙, or 知識, and does not treat an entire existing document as incorrect. Negative preference is updated once per minibatch using a random eligible pair; the existing replay and stabilization steps remain unchanged.

For reproducibility, trainer arguments `--negative-repairs`, `--negative-weight` and `--negative-margin` are available. Set `--negative-weight 0` for the positive-only baseline.

## Windows
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.43-negative-teacher-signal
python -m unittest -v test_negative_teacher_signal_v013588243.py test_good_repair_confirmation_v013588241.py
python chat_gui.py
```

No extra manual commands are needed: answer rejection -> referenced fallback -> `/good` -> automatic online training with paired positive and negative teacher signals. Without `/good` the pending repair is canceled and cannot participate in negative training.

Important limitations: Current GUI records the topic (e.g. 宇宙) rather than full question, so contrastive training may not match the Evidence candidate's original long prompt; this mismatch needs follow-up. The positive excerpt is explicitly user endorsed, not independently audited. Training currently reloads a checkpoint without a rigorous holdout gate; back up models and measure before/after candidate generation and regressions. Merely suppressing the bad response does not prove that a valid correct response will be generated.
