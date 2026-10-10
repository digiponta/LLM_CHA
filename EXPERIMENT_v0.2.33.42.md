# v0.2.33.42 — Held-Out Clarification Policy Probe

Compares the **unmodified v0.2.33.39** bridge with the **v0.2.33.40 interruptible** bridge on exactly the same 12 researcher-authored, previously unused Japanese follow-up scenarios. Both arms use their actual deterministic policy and isolated temporary JSON shadow store; there is no data migration or modification of production knowledge.

Evaluate **route** and **status** separately (plus both correct). A route match alone may conceal a wrong outcome: for example a Japanese candidate answer may be routed to reference-resolution yet fail to produce `confirm`. Probe categories: new explicit goals, indirect topic switches, Japanese alias replies, and novel reference paraphrases. **No inferred results are claimed before running the script.**

### PowerShell

```powershell
git fetch origin
git switch v0.2.33.42
git pull origin v0.2.33.42
python -m py_compile heldout_clarification_eval_v023342.py
python -m unittest -v test_heldout_clarification_eval_v023342.py test_clarification_policy_eval_v023341.py
python heldout_clarification_eval_v023342.py
```

Report: `results/heldout_clarification_eval_v023342.json` (refuses overwrite). Inspect per-case expected/actual route and status, not only aggregate.

### Scientific caveat

'Held-out' means new relative to earlier handcrafted v0.2.33.41 fixtures, **not** a representative independently annotated dialogue corpus. Some gold labels reflect design goals for incomplete functionality. These are diagnostic probes for a rule-based controller, not measures of general Japanese understanding. A next iteration should create human-labeled multi-turn dialogues and introduce a policy-independent evaluation set before tuning parsers further. No stable runtime, Semantic Memory training store, or neural checkpoint is modified.
