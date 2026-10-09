# LLM_CHA v0.2.30.5 — Recovery Command & Target Probability Diagnostic

Status: source and tests committed to GitHub; local unit tests and RTX GPU execution pending.

## Research question

v0.2.30.4 Recovery SFT: CONTINUE 0/6 and RESTART 0/6 lexical
topic coverage on the six curated prompts. Is it a failure to respond
to the recovery command, a failure to assign probability to the correct
answer, or mainly a free-generation problem?

**No new training**: compare existing v0.2.30.2 Continuation and v0.2.30.4
Recovery checkpoints. Evaluate 6 CONTINUE / 6 RESTART examples per model.

1. **Command-conditioned target sensitivity**: for each identical prefix
   and identical reference answer, score teacher-forced answer NLL with
   the actual command vs the other command substituted, keeping all
   other words the same. Positive \`Δcommand = swapped_NLL - matched_NLL\`
   means the intended command makes that answer more likely. This is
   *not* proof that the model recognizes the correct mode on its own.
2. **Answer likelihood**: teacher-forced mean token NLL of the intended
   response, including EOS, using the full preformatted multi-turn
   prompt; compare models within the same test case.
3. **Candidate ranking**: compare target answer NLL against generic
   answers "そうですね。" and "そうなんですか?" at the exact same prompt.
   Normalized mean NLL can exhibit candidate-length bias, so this is a
   limited diagnostic rather than complete response quality.
4. **Free generation**: show topic lexical hits as in v0.2.30.4, keeping
   them separate from teacher-forced metrics.

## Execution

\`\`\`powershell
git fetch origin
git switch v0.2.30.5
git pull origin v0.2.30.5
python -m unittest -v test_recovery_understanding_v02305.py
python diagnose_recovery_understanding_v02305.py
\`\`\`

Output: \`results/recovery_diagnosis_v02305.jsonl\`
(2 checkpoints × 12 questions = **24 JSONL records**).

## Decision guide

- Target NLL falls but free generation remains generic: investigate
  decoding, response modes and output distribution.
- Positive command sensitivity and target outranks generic: there is
  evidence of *instruction-conditioned preference*, not autonomous mode choice.
- Neither target likelihood nor command sensitivity improves: revise
  instruction representation, training target construction and data scale.
- Check every raw response for topicality and grammar; lexical indicators
  cannot establish sentence-level coherence.

The curated prompts were used for SFT of v0.2.30.4, so all measurements
on them are *in-sample*. No unseen-topic or independent command
generalization claim is supported by this experiment.
