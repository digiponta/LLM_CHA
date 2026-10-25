# LLM_CHA v0.9.7.36 — Three-model emotion generation evaluation

The v0.9.7.35 conditioned checkpoint trained successfully, but lower
training/holdout NLL **does not establish improved dialogue generation**.
This diagnostic compares frozen checkpoints without training:

- **Baseline:** original v9.4 Nagato checkpoint, ordinary prompt.
- **Daily:** v0.9.7.32 unconditioned daily SFT, ordinary prompt.
- **Conditioned:** v0.9.7.35 semantic-prefix SFT, ordinary prompt,
  correctly conditioned prompt, and deliberately swapped-emotion prompt.

There are **30 v0.9.7.32 development holdout prompts** and **7 explicit
challenge prompts**. 5 generations per case = 185 outputs. Exact
reference matches, conservative strategy gate, and response changes
under intentionally incorrect emotion markers are included in the
JSON report. A changed response under a swapped marker **does not
prove correct use of meaning**, and the whitelist gate is not a
semantic scoring model. Examine the raw output texts.

The 30 evaluation examples were developed during earlier iterations
and must not be described as a new independent final benchmark.
No checkpoint, Semantic Memory, or online chat behavior is changed.

## Windows PowerShell

```powershell
git fetch origin
git switch --track origin/v0.9.7.36

python -m unittest -v `
  test_emotion_generation_v09736.py `
  test_emotion_quality_gate_v09735.py

python evaluate_emotion_generation_v09736.py `
  --baseline model/model-llm-try-nagato-chat-v94.pt `
  --daily model/model-llm-cha-semantic-daily-v09732-experimental.pt `
  --conditioned model/model-llm-cha-emotion-conditioned-v09735.pt `
  --tokenizer model/tokenizer-v0.7-bpe.json `
  --output results/emotion_generation_v09736.json
```

The output file must not already exist. Run on NVIDIA GPU by default;
use `--cpu` for CPU evaluation.

Review:
1. Correct vs swapped-condition outputs on each of the 37 prompts.
2. Confusion of positive/negative sentiments and mixed feelings.
3. Protected identity and greeting challenges.
4. Excessive reuse of a single answer and low-confidence garbage.
5. Validity of the conditioned template labels versus runtime detector
   labels; inconsistent taxonomies limit interpretability.
