# v0.2.33.24 — Copy Output Bias & EOS Separation

## Context

v0.2.33.23 showed known-ID replacement Top-1 rates of 9/12 (short) and 8/12 (long, Combined), while held-out-ID replacements were 0/12 in both Combined conditions. EOS at the correct length was Top-1 for 7/12 long Combined examples, under teacher forcing. These are small diagnostics, not proof of a missing specific circuit.

## Frozen model comparisons

Load `model/model-llm-cha-algorithmic-copy-v023320.pt` and `model/token_copy_factorial_v023322/combined.pt` without changing their parameters. Evaluate common fresh synthetic sequences, 20 each:
- Short, known IDs: length 2–8
- Long, known IDs: length 12–18
- Novel IDs: length 2–8, tokens 88–103
- Mixed IDs: length 2–8, known + novel IDs

Compare five decoding conditions:
1. `normal`: ordinary greedy token generation.
2. `source_candidates`: restrict next-token choice to source IDs plus EOS; reveals whether large-vocabulary competition contributes.
3. `known_length`: disallow EOS before the gold source length, then force EOS exactly there; isolates termination timing under an external oracle.
4. `source_and_length`: both candidate restriction and gold-length EOS timing.
5. `position_oracle`: force the gold source token for each step; **tautological upper bound, never a model capability metric**.

Report exact token sequence including EOS and content accuracy at the gold length. Compute gold-token probability and rank at a teacher-forced middle position, correct EOS probability and rank, mean known-ID vs unseen-ID logits, and input-embedding/output-head norms and cosine by ID group.

## Commands

```powershell
git fetch origin
git switch v0.2.33.24
git pull origin v0.2.33.24
python -m unittest -v test_copy_output_bias_eos_v023324.py
python diagnose_copy_output_bias_eos_v023324.py
```

Produces `results/copy_output_bias_eos_v023324.json`; refuses overwriting an existing report.

## Interpretation

Candidate restrictions and gold length/EOS use *external knowledge*; positive improvements reveal specific bottlenecks but are not normal autonomous performance. Source candidate restriction can fail even with a perfect position match if the model ranks a different source token higher. The position oracle simply copies the provided source; its success is uninformative as a learned skill.

Do not claim causal attribution to attention from these descriptive statistics. No changes to DSS, Semantic Memory, Semantic Bridge, or prior checkpoints.
