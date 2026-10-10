# v0.2.33.9 — Input-to-Output Copy Learning

## Question

Can the small LLM_CHA autoregressive Transformer reproduce a sentence explicitly written in its prompt, including unseen strings and unseen compositions of known words?

This isolates **literal copying**, not semantic understanding or semantic internalization. Existing DSS, Semantic Memory, Bridge and every earlier model checkpoint are unchanged.

## Protocol

- Start from original frozen-reference checkpoint `model/model-llm-cha-response-quality-v0221.pt` and fine-tune a *new* output checkpoint with response-only cross entropy.
- 20 diverse authored sentences for train, 5 other sentences for validation and 8 withheld sentences for free-generation evaluation.
- 4 trained examples are also evaluated to distinguish memorization from transfer.
- Evaluation includes unseen sentences, novel combinations and longer responses.
- Existing dialogue replay is sampled during training, and the best validation-NLL model is selected with early stopping. Retention is not verified by replay loss alone.
- Copy accuracy uses exact decoded-string matching. A near miss is a literal failure even if semantically close.
- The evaluation examples are bundled openly in the repo: this is an exploratory benchmark, not a sealed untouched dataset. Because the model tokenizer uses subwords, novel word sequences are not necessarily novel tokens.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.9
git pull origin v0.2.33.9

python -m unittest -v test_input_output_copy_learning_v02339.py
python input_output_copy_learning_v02339.py train --epochs 25 --patience 5
python input_output_copy_learning_v02339.py evaluate
```

Outputs:
- `model/model-llm-cha-copy-v02339.pt`
- `results/copy_learning_train_v02339.json`
- `results/copy_learning_eval_v02339.json`

## Decision criteria

- Seen copies work / unseen fail → likely memorization, no generalized copying.
- Short unseen work / long unseen fail → length or attention/prefix-generalization issue.
- No seen copies work despite falling NLL → inspect tokenizer roundtrip, answer-mask alignment, generation stop/EOS and prompt mismatch, then adjust training/corpus.
- Unseen copies work → move to Content Extraction without assuming true semantic understanding.

**Limits:** 20 training examples is an intentional minimal diagnostic, not sufficient to build a production text copying model. The generator uses the existing `CheckpointGenerator.generate` decoding defaults, so generation settings and tokenization may materially affect results.
