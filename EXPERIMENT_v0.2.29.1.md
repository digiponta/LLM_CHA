# LLM_CHA v0.2.29.1 — Topic-Grounded SFT Experiment

Status: GitHub implementation complete; GPU training and independent evaluation pending.

## Rationale
v0.2.29.0 raw baseline/persistence evaluation:
- exact topic mentions: train 0/12, holdout 0/6 for both models
- baseline generic replies: train 7/12, holdout 4/6
- persistence generic replies: train 6/12, holdout 4/6

The 12 curated train rows have NEVER been incorporated into the existing checkpoints.

## Controlled arm
Same initial v0.2.21 checkpoint, 3000 replay and 90 anchor exposures, same
optimizer and 3 epochs as v0.2.28. Replace **216 existing context exposures**
(18 topic examples × 12 repetitions) with **216 curated grounded exposures**
(12 topic examples × 18 repetitions). This is a substitution, not a
same-dataset loss-only ablation. The new topic distribution is different,
and gains cannot be attributed to the objective alone.

Use original context-only initialization + continuation loss:
L = L_normal + 0.5 L_first8 + 0.5 L_after8.

Existing trainer uses --preformatted-prompts across all data. New grounded
single-turn input is converted from 'カレーについて...' into a *preformatted
prompt body* '人: カレーについて...' to match raw evaluation prompt
'人: {question}\\nAI: '. Do not add 'AI: ' in the user field.

## Run
```powershell
git fetch origin
git switch v0.2.29.1
python -m unittest -v test_topic_grounded_sft_v02291.py
python prepare_topic_grounded_v02290.py
python prepare_topic_grounded_preformatted_v02291.py
python run_topic_grounded_sft_v02291.py --dry-run
python run_topic_grounded_sft_v02291.py
python evaluate_topic_grounded_v02290.py --model baseline=model/model-llm-cha-v0227-baseline.pt --model persistence=model/model-llm-cha-context-persistence-v0228.pt --model grounded=model/model-llm-cha-topic-grounded-v02291.pt --out results/grounded_compare_v02291.jsonl
```

## Decision gate
Evaluate train and holdout separately; exact mentions are a **lexical proxy**,
not semantic accuracy or grammaticality. Manually inspect generated content,
generic fallback, EOS lengths, and preserve persona/general-chat probes.
Topic leakage is controlled *within the curated 12/6 dataset*, but pre-existing
3000 replay pairs may reference holdout topics, so this is NOT a guaranteed
fully unseen benchmark. For a truly independent holdout, audit and filter all
training sources before making generalization claims.

Re-training from v0.2.21 avoids using v0.2.28 checkpoint as the initialization,
and helps fairer comparison with v0.2.28 under matched sample exposure counts.
No performance improvement should be claimed until actual runs.
