# LLM_CHA v0.2.33.18 — Copy Generalization Curriculum

## Background

v0.2.33.16 achieved **80/80** held-out exact copies within a narrow color/object/place/action grammar, but v0.2.33.17 found **0/40** exact copies on the six out-of-distribution groups (eight new-vocabulary, eight new-syntax, four longer, four multiple-sentence, eight symbol/numeric and eight original benchmark cases). This indicates limited transfer beyond the synthetic training grammar, not an identified Transformer computation bug.

## Experimental design

Starting with the **frozen v0.2.33.16 checkpoint** as initialization (kept unchanged), use one staged training run:

| Stage | Examples introduced | New train / val / test |
|---|---|---|
| Lexical | New color, object or location in existing sentence form | 320 / 48 / 48 |
| Syntactic | Fronted location or connective-prefixed clause | 320 / 48 / 48 |
| Sequence | Two-clause output ending in 「確認します。」 | 320 / 48 / 48 |

The generator uses distinct strings and a seeded deterministic split. Previous restricted-grammar validation/test strings are excluded from stage training. Stage order is lexical → syntactic → sequence; later stages replay all preceding curriculum **training** examples. Each stage runs two epochs by default, so there are up to 3,840 gradient steps; the experiment may take a while on a single GPU.

Selection occurs **only** using aggregate response-only validation NLL over the 144 curriculum validation examples; a saved model is selected from all stage/epoch states. Final tests are evaluated **only after** selecting a checkpoint. The final result also evaluates 20 old validation and 20 old test grammar samples to check retention. **Do not reuse** the v0.2.33.17 OOD probe questions for training and do not tune against final test results.

This is still constrained-template learning: the novel lexical items appear during curriculum training; a high stage-test accuracy proves new *combinations* in expanded templates, not arbitrary unseen vocabulary or free-form Japanese copying. Symbol/numeric robustness is intentionally reserved for a later stage because NFKC may alter canonical text fidelity.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.18
git pull origin v0.2.33.18
python -m unittest -v test_copy_generalization_curriculum_v023318.py
python copy_generalization_curriculum_v023318.py --epochs-per-stage 2
```

Outputs:
- `model/model-llm-cha-copy-curriculum-v023318.pt`
- `results/copy_curriculum_v023318.json`

The script refuses overwriting an existing checkpoint or report; use new `--output` and `--report` paths for reruns. This checkpoint remains experimental; DSS, Semantic Memory and Bridge remain unchanged.

## Evaluation priority

Compare per-stage train, validation and test exact-copy accuracy and retention of original grammar. Only after this should fresh, newly authored OOD tests (lexical, syntax, multi-sentence, long strings and symbols) be run, without leaking the original OOD test strings into training or checkpoint selection.
