# LLM_CHA v0.2.29.2 — Topic Contrastive Generation Analysis

**Status:** code committed; local unit tests and GPU measurements pending.
Existing checkpoints are preserved.

## Motivation

v0.2.29.1 changed output patterns without exact topic mention improvements
(train 0/12, holdout 0/6). For example, the grounded model generated a
space-related sentence in response to both 宇宙探査 and 歴史小説.

## Diagnostic

For each input topic, score the answer associated with that topic and
five competing answers associated with other topics using teacher-forced
mean NLL (including EOS). All candidates are compared under the *same*
input prompt. Scores are grouped by train vs holdout split. For train,
the FIRST reference answer per topic is used as a candidate in every
comparison, avoiding duplication of candidates for the two paraphrased
questions per topic. Holdout uses its own six candidate references.

Interpretation:
- margin = lowest wrong-topic NLL minus correct-topic NLL
- positive margin: correct answer ranks above every distractor
- negative margin: one or more wrong-topic answers outrank correct
- correct_at_1: highest-ranked answer belongs to the input topic

NLL is length-normalized by assistant token count; however different
phrasing and candidate lengths still bias rankings. This is **candidate
selection under teacher forcing**, not autonomous answer generation.
Candidate texts contain the topic term by construction. An all-candidate
ranking is not an independent semantic entailment metric.

## Run

```powershell
git fetch origin
git switch v0.2.29.2
python -m unittest -v test_topic_contrastive_v02292.py
python prepare_topic_grounded_v02290.py
python analyze_topic_contrastive_v02292.py
```

Output: `results/topic_contrastive_v02292.jsonl`.
Three models × (12 training prompts + 6 holdout prompts) = 54 ranked
comparisons, each against six topic candidates.

## Decision gate

If grounded model ranks the correct answer in most train prompts but free
generation still fails, prioritize decoding/exposure-bias diagnostics rather
than assuming topic encoding is absent.

If correct-answer ranking also fails after grounded SFT, consider
v0.2.30 controlled contrastive response selection objective (with negative
topic pairs), but design a balanced objective and holdout leakage audit first.

If only holdout ranking fails, focus on topic generalization before adding
contrastive loss.

No GPU measurements or performance claims at time of commit.
