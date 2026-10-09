# LLM_CHA v0.2.30.1 — Explicit Topic Prefix Supervision

Status: committed, GPU test/evaluation pending.

The v0.2.30.0 experiment produced exactly the same training and generated outputs
as v0.2.29.1; its proposed data change was a no-op because the old answers
already began with their topic names. This experiment guarantees 12/12 changed
answers by adding an explicit lead: "宇宙探査について説明するね。" followed by
the full old answer. Prompts and the old answer content remain unchanged.

**Important limitations:** Adding a formulaic lead can produce repetitious
or unnatural text (e.g., "カレーについて説明するね。カレーでは..."). An exact
topic-string increase alone is not evidence of semantic relevance. Only
12 curated examples are included, with 18 exposures each; compare against
v0.2.29.1 on the same generated prompts and inspect response quality.
The same historical replay is retained; holdout is not guaranteed globally
unseen until a full replay contamination audit.

## Run

```powershell
git fetch origin
git switch v0.2.30.1
python -m unittest -v test_topic_prefix_v02301.py
python prepare_topic_grounded_v02290.py
python prepare_topic_prefix_v02301.py
python run_topic_prefix_sft_v02301.py --dry-run
python run_topic_prefix_sft_v02301.py
python evaluate_topic_grounded_v02290.py --model grounded=model/model-llm-cha-topic-grounded-v02291.pt --model prefix=model/model-llm-cha-topic-prefix-v02301.pt --out results/topic_prefix_compare_v02301.jsonl
```

Expected data check: "Topic prefix changed: 12/12"; run script
revalidates exact rows before launch. Training sample exposure remains
3000 replay + 216 prefix + 90 persona anchors = 3306/epoch, same initial
checkpoint as v0.2.29.1. Unlike v0.2.30.0, this is a true changed-data arm.

Measure lexical topic mention (train/holdout), naturalness, off-topic
errors, validation loss, candidate ranking and persona retention.
Do not claim quality improvements until measurement.
