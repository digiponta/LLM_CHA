# LLM_CHA v0.2.29.0 — Topic-Grounded Generation Dataset & Evaluation

Status: code committed, GPU tests/evaluation not yet run. Checkpoints unchanged.

## Rationale

Earlier v0.2.28.2 diagnostics showed longer responses when EOS was suppressed
but little corresponding increase in topical grounding. Begin a new
evidence-centered generation evaluation instead of immediately adding loss.

## Protocol

- 6 train topics × 2 compact assistant responses = 12 curated SFT examples
- 6 disjoint holdout topics × 1 response = 6 independent-topic evaluation cases
- Every assistant response includes an explicit topic phrase.
- `train.jsonl` is an **optional future** augmentation fixture, not part of
  any current model. Holdout references MUST NOT be used for training.
- `eval.jsonl` includes both train and holdout examples with provenance.
- Metrics: exact normalized topic string mention, generic-response proxy,
  repeated-span proxy, generated token count, and raw text. Exact mention is
  necessary for this simple lexical metric but is neither sufficient for
  factual quality nor a full semantic grounding score. Some relevant replies
  can omit the literal topic and score false.

## Commands

```powershell
git fetch origin
git switch v0.2.29.0
python -m unittest -v test_topic_grounded_v02290.py
python prepare_topic_grounded_v02290.py
python evaluate_topic_grounded_v02290.py
```

Outputs:
- data/topic_grounded_v02290/train.jsonl
- data/topic_grounded_v02290/holdout.jsonl
- data/topic_grounded_v02290/eval.jsonl
- results/topic_grounded_eval_v02290.jsonl

## Decision gate before v0.2.29.1 training

Review baseline raw texts and the train/holdout gap, then decide whether
grounded-example replay augmentation or generated-prefix recovery is the first
experiment. Preserve regular conversation/persona probes. A lexical topic
mention gain alone does not prove a better answer. Tests and inference must
be run by the user in the GPU environment before results are claimed.
