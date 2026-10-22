# LLM_CHA v0.7.4 — Adapter Quality & Knowledge Promotion Gate

Two separate operations, intentionally not coupled:

1. **Read-only evaluation** of Frozen Base, Trusted Adapter (untrained baseline
   in v0.7.3), and Experimental Adapter on PENDING Candidate question-answer pairs.
   Metrics are teacher-forced answer-token NLL and token top-1 accuracy, **not**
   free-form conversation correctness. When approved records exist, up to 20
   serve as a protected probe set.
2. **Explicit, operator-triggered promotion** of a PENDING knowledge record,
   requiring reviewer identity, an evidence description and exact
   `--decision APPROVE`. Preserves source_id. No adapter weights copied.

## Windows

```powershell
git fetch origin
git switch --track origin/v0.7.4
python -m unittest -v test_knowledge_promotion_v074.py test_dual_adapters_v073.py
python evaluate_dual_adapter_v074.py `
  --base model/model-gpu-v1.6.2-online.pt `
  --adapter results/adapter_sandbox_v073/experimental-adapter.pt `
  --report results/adapter_quality_v074.json
```

Review the resulting JSON. A negative
`candidate_nll_delta_experimental_minus_base` indicates improvement
only on teacher-forced candidate tokens; it does not grant approval.

### Separate human approval (do NOT run without independent verification)

```powershell
python knowledge_promotion_gate_v074.py `
  --id <candidate-id> `
  --reviewer <reviewer-label> `
  --evidence "Description of independently checked source" `
  --decision APPROVE
```

This mutates the v0.7.1 JSONL stores. Do not promote the example test phrase
simply because the sandbox has learned it.

## Limitations

- v0.7.4 is an experimental offline evaluator and manual command; it does
  not change `chat.py`, existing Runtime, or production model weights.
- No automatic quality threshold or factual-verification automation.
- The initial Trusted Adapter remains untrained: it is a control condition.
- Approval audit is appended after store changes; a crash may omit audit.
  Cross-file transactional consistency and concurrency locks are deferred.
- Human review metadata is operator input, not an independently verified
  identity. A production-grade approval service must authenticate reviewers.
