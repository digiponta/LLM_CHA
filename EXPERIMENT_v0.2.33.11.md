# v0.2.33.11 — Response Initiation Diagnostics

## Purpose

v0.2.33.10 showed normal tokenizer roundtrip and training-target alignment but severe first-token ranking errors even on trained copy sentences. Test **where free autoregressive copying fails**, without altering checkpoints, DSS, Semantic Memory or Bridge.

## Conditions

For the same exact input sentences, compare:
- original copy instruction prompt `人: ...\n文章: ...\nAI: ` (Raw)
- short copy prompt `文章: ...\n出力: ` (Short)
- 0, 1, 3 *gold answer tokens* supplied after the prompt (for both forms)
- Base checkpoint vs trained copy checkpoint

Per condition report first next-token rank/probability/top-1, contiguous exact correct token run, full token match including EOS, generated surface string and EOS stop.

**Important:** Gold prefixes are not autonomous generation, and differ from simply inserting whole Japanese characters because BPE token boundaries matter. Tokenized prompt and answer are concatenated like response-only SFT to align with prior experiments.

## Windows commands

```powershell
git fetch origin
git switch v0.2.33.11
git pull origin v0.2.33.11
python -m unittest -v test_response_initiation_diagnostics_v023311.py
python response_initiation_diagnostics_v023311.py
```

Output: `results/response_initiation_v023311.json`.

If even supplying 3 correct tokens does not extend the faithful continuation length, a sole *first-token* explanation is unsupported. Compare ranking across Raw and Short to detect prompt dependence and decide whether the next priority is initiation SFT, sequence-level copy, or prompt-alignment changes. Do not interpret a rank improvement as meaning understanding.
