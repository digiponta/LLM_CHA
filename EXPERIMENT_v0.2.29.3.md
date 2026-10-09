# v0.2.29.3 — Candidate Generation & Reranking

Status: code committed; tests and GPU evaluation not yet executed.

## Motivation
v0.2.29.2 showed topic-conditional candidate ranking improves with grounded
SFT (train top-1 7/12 vs baseline 3/12; holdout 2/6 vs 1/6),
while direct greedy topic mentions remain 0/12 and 0/6.

## Experiment
Each of 18 prompts gets:
- one greedy response
- eight independent samples (temperature 0.8, top-k 40, seeds 42–49)
- identical raw prompt template as v0.2.29.0
- no candidate injected from training references
- two selectors on the *same generated candidate set*:
  * NLL-only: lowest teacher-forced response NLL (includes EOS)
  * lexical oracle-assisted: literal input topic mention first, then
    avoid exact generic response / repeated spans, then NLL

Metrics: candidate pool oracle exact-topic availability, greedy exact-topic
mention, NLL-selector mention, lexical-selector mention; train and holdout
separately. Lexical reranking is a *deliberately optimistic lexical baseline*:
it uses the topic string explicitly and DOES NOT establish neural semantic
grounding or answer factual accuracy. A topic term copied into an
ungrammatical sentence is still a positive lexical hit.

## Run
```powershell
git fetch origin
git switch v0.2.29.3
python -m unittest -v test_candidate_reranking_v02293.py
python prepare_topic_grounded_v02290.py
python evaluate_candidate_reranking_v02293.py
```

Output: results/candidate_reranking_v02293.jsonl.

Decision gate:
- If candidate oracle availability is low, prioritize generation/training.
- If availability is high but NLL ranking fails, consider dedicated
  selection/re-ranking training; compare actual semantic quality manually.
- If train only improves, test topic generalization and broader holdouts.
- Preserve checkpoints and general conversation/persona results.
