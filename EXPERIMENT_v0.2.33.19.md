# LLM_CHA v0.2.33.19 — Independent OOD Transfer Evaluation

## Purpose

v0.2.33.18 reported 144/144 test exact copies inside its expanded synthetic curriculum (lexical, syntactic, sequence). In v0.2.33.17, the earlier v0.2.33.16 model had only 20/20 in-grammar success and 0/40 outside the original grammar. Here we test whether curriculum training transfers to **newly authored, template-outside** examples, without modifying either checkpoint.

## Evaluation

Two frozen models, identical tokenization and greedy generation with no repetition penalty:
- **Baseline** `model/model-llm-cha-general-copy-v023316.pt`
- **Curriculum** `model/model-llm-cha-copy-curriculum-v023318.pt`

Three disjoint evaluation categories are kept conceptually distinct:
1. **In-grammar control:** 20 deterministic old held-out test sentences.
2. **Fresh OOD:** 29 newly authored probes: six new lexicon, six new syntax, three long context, four multiple sentences, six numeric/ASCII, four Unicode fidelity.
3. **Reused diagnostic OOD:** the 40 known v0.2.33.17 OOD examples, *separately* labeled as previously inspected. They do **not** qualify as a clean independent holdout.

Each case retains strict exact-text comparison, token sequence comparison including EOS, length and initial-token-match diagnostics, and tokenizer roundtrip.

## Windows commands

```powershell
git fetch origin
git switch v0.2.33.19
git pull origin v0.2.33.19
python -m unittest -v test_independent_ood_transfer_v023319.py
python evaluate_independent_ood_transfer_v023319.py
```

Output: `results/independent_ood_transfer_v023319.json`.

The script is **evaluation only**, refuses overwrite, and does not train, select, promote or alter the checkpoints, DSS, Semantic Memory or Bridge.

## Interpretation

- Curriculum beats baseline on fresh OOD: some cross-template transfer is observed; examine per-class failure modes before claiming generic copy capability.
- Both fail on new structures: expanded template fitting is insufficient; next study should target character/byte copying, algorithmic generalization and length robustness.
- In-grammar retention falls: investigate catastrophic forgetting before further SFT.
- Unicode roundtrip fails: tokenizer NFKC normalization prevents strict character-identity even if sequence modeling were perfect.

Small hand-authored tests are diagnostic, not population-wide performance estimates.
