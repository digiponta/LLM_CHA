# v0.2.30.0 — Topic-Conditioned Prefix Learning

Status: implementation committed; Windows unit tests, dry-run, GPU training and free-generation evaluation pending.

## Hypothesis
v0.2.29.3 generated candidate pool contained an exact topic mention in only
2/12 train and 0/6 holdout cases, even after 8 samples per prompt.
Contrastive ranking alone is therefore unlikely to recover good answers.

Test a minimal *training intervention*: every one of the 12 curated
training responses starts with the input topic string. No runtime topic
copying, forced-prefix decoding or contrastive loss is used. This encourages
the language model itself to emit the topic.

## Controlled comparison
- Initialization: SAME v0.2.21 checkpoint used by v0.2.29.1
- Replay: 3000
- Persona anchors: 9 x 10 = 90
- Topic rows: 12 x 18 = 216, same prompt texts as v0.2.29.1
- 3 epochs; 2 trainable blocks; unchanged learning rates
- Loss: context-specific first-8 and post-8 auxiliary losses inherited
  unchanged from v0.2.28
- Only training response opening changes relative to v0.2.29.1.
- Holdout examples are excluded from the new corpus (although full historical
  replay contents have not yet been audited for topic leakage).

## Run on Windows
```powershell
git fetch origin
git switch v0.2.30.0
python -m unittest -v test_topic_prefix_v02300.py
python prepare_topic_prefix_v02300.py
python run_topic_prefix_sft_v02300.py --dry-run
python run_topic_prefix_sft_v02300.py
python evaluate_topic_grounded_v02290.py --model grounded=model/model-llm-cha-topic-grounded-v02291.pt --model prefix=model/model-llm-cha-topic-prefix-v02300.pt --out results/topic_prefix_compare_v02300.jsonl
```

## Evaluation
Compare exact-topic mentions, actual sentence quality, off-topic responses,
baseline conversation/persona tests, and previous validation NLL. Do not
equate literal topic echo with factuality or semantic correctness. If
training-topic mention improves but holdout does not, investigate copying
versus generalization. No successful GPU result is claimed before logs.
