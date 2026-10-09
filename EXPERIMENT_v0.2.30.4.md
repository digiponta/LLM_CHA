# LLM_CHA v0.2.30.4 — Continue vs Restart Recovery SFT

Status: GitHub files committed; Windows unit tests, GPU training and comparison NOT yet run.

## Why
v0.2.30.3 diagnosis: both self-generated and reference-first-8-token
prefixes had poor topical continuation. The newly generated suffix had
lexical topic coverage 0/12 vs 1/12 (prefix model), and likewise
0/12 vs 1/12 (continuation model); holdout 0/6 for both conditions.
Merely forcing a reference prefix is not enough.

## Careful scope
The present experiment **does not autonomously predict whether the
prefix is damaged**. It learns from explicitly labelled corrective
dialogue commands [CONTINUE] or [RESTART] to disambiguate the two modes.
The classification helper uses hand-curated safe stems and treats other
prefixes as needing restart. It is a data-preparation rule, not a learned
semantic judge. Free-running suffix recovery from an uninterrupted
assistant text will require a later separate experiment.

Curated 12 examples:
- 6 CONTINUE cases: user prompt, assistant's usable on-topic opening,
  explicit user command to continue, target on-topic continuation.
- 6 RESTART cases: user prompt, observed wrong/off-topic answer,
  explicit user command to answer again, target complete replacement
  answer. The broken text is not prepended to the clean answer.

Training runs from same v0.2.21 base checkpoint as previous v0.2.29.1
experiments, with 3000 replay + 12 recovery x18 + 90 anchors = 3306
exposures per epoch; 3 epochs, identical v0.2.28 persistence loss.
This changes the sample distribution so it is not a pure loss ablation.
The six curated holdout topics are not used to prepare these twelve
examples; the original 3000 replay rows have not been audited for
topic contamination.

## Windows
```powershell
git fetch origin
git switch v0.2.30.4
python -m unittest -v test_prefix_recovery_v02304.py
python prepare_prefix_recovery_v02304.py
python run_prefix_recovery_sft_v02304.py --dry-run
python run_prefix_recovery_sft_v02304.py
python evaluate_prefix_recovery_v02304.py
```

Output:
- data/prefix_recovery_v02304/train_preformatted.jsonl
- data/prefix_recovery_v02304/mode_audit.jsonl
- model/model-llm-cha-prefix-recovery-v02304.pt
- results/prefix_recovery_eval_v02304.jsonl

## Interpretation and next step
Check CONTINUE and RESTART separately for topic vocabulary, correctness,
grammar and context coherence. The lexical check is a weak proxy, not
evidence of fluent semantic repair. Since the prompts explicitly contain
recovery instructions, this does not test spontaneous detection, seamless
continuation or unseen-topic generalization. For that, first create
independent evaluated corrupt prefixes, then a separate router/rewrite
diagnostic, carefully distinguishing a new response from an appended
suffix. Preserve chat/persona regression.
