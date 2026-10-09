# LLM_CHA v0.2.30.3 — Self-Generated Prefix Continuation Diagnosis

Status: GitHub code committed; GPU experiment pending.

## Hypothesis
In v0.2.30.2, two-sentence training did not yield topical second
sentences in raw generation (0/12 train and 0/6 holdout), despite
producing multiple sentence-like fragments in some cases. Diagnose
whether incorrect self-generated openings drive continuation errors.

## Conditions
For each of 18 prompts, two existing checkpoints (v0.2.30.1 and
v0.2.30.2) use identical decoding, max-new-token limits and prompt.
Condition 1: **self_prefix**: autonomously generate the first eight
tokens, then continue from those tokens with no insertion or rewriting.
Condition 2: **reference_prefix**: force the first eight tokens of
the fixture reference answer, then continue. The reference tokens are
teacher-provided and must NEVER be counted as successful free generation.

Report topical-lexical indicators for the **newly generated suffix**,
along with topic-bearing second-sentence proxies. The latter includes
the forced prefix, so suffix-only coverage is more trustworthy for
separating the two conditions. Human review of full generated answers
is required for grammatical, contextual and factual assessment.
The same six holdout topics are not guaranteed wholly absent from
the 3000 replay source; no generalization claim without corpus audit.

No fine-tuning is performed and no self-correction success is claimed.
This is a prerequisite diagnostic for possible v0.2.30.4
Generated-Prefix Recovery Training.

## Run
```powershell
git fetch origin
git switch v0.2.30.3
python -m unittest -v test_self_prefix_continuation_v02303.py
python prepare_topic_grounded_v02290.py
python diagnose_self_prefix_continuation_v02303.py
```

Output: `results/self_prefix_continuation_v02303.jsonl`.
Expected 2 models × 18 questions × 2 prefix conditions = 72 rows.

## Decision
- Self-prefix fails, reference-prefix succeeds: prioritize recovering
  generation from bad prefixes, while guarding against forced-prefix bias.
- Both fail: improve continuation training or model capacity/data.
- Both succeed on seen but not holdout: prioritize topic generalization.
- Review whether tokens crossing Japanese word boundaries cause awkward
  splices; do not mistake a fragment for a natural continuation.
