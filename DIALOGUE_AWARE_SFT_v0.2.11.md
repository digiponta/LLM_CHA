# LLM_CHA v0.2.11 — Dialogue-Aware SFT Pilot

**Goal:** Improve actual next-turn generation, not just filtering/reranking. Branch derived from v0.2.10; preserves the v0.2.8 checkpoint and existing gates.

## Scope

- `prepare_dialogue_sft_v0211.py` constructs preformatted multi-turn user prompts with target replies that **address prior answers** and **develop the topic**, rather than repeating questions. Six small hand-authored training conversations are expanded to 24 transition examples and repeated 30×, mixed with up to 3000 randomly selected v0.2.8 training examples.
- Two separate *synthetic*, topic-disjoint conversations are used as a validation split, never inserted into training.
- Persona identity anchors are replayed via the existing SFT trainer using the v0.2.8 preformatted anchors.
- `train_dialogue_sft_v0211.py` starts from `model-llm-cha-quality-v028.pt`, uses low LRs, and saves a separate `model-llm-cha-dialogue-v0211.pt`.
- **Caution:** Just 6 authored sessions are far too little for robust generalization. Their 30x repeat can lead to overfitting. Validation is synthetic, not an independent natural-language final benchmark. Reporting loss alone is insufficient.

## Local commands

```powershell
git fetch origin
git switch --track origin/v0.2.11
python -m unittest -v test_dialogue_sft_v0211.py test_candidate_reranker_v0210.py test_dialogue_state_v029.py
python prepare_dialogue_sft_v0211.py
python train_dialogue_sft_v0211.py --dry-run
python train_dialogue_sft_v0211.py
```

For comparison with the previous checkpoint, keep runtime/gates the same:

```powershell
python chat.py --model model/model-llm-cha-dialogue-v0211.pt --tokenizer ..\LLM_TRY\model\tokenizer-v0.7-bpe.json --character nagato --dialogue-history-turns 2 --probe-count 3 --temperature 0 --show-context --show-candidate-ranking --show-dialogue-state --show-conversation-diagnostics
```

Probe (train-like): `最近、小説にはまっています`, `SFです`, `その話、続けて`.
Probe (heldout topics): `最近、写真を撮っています`, `夜景です`, `街並みです`, `その話、続けて`. Add truly unseen human-written conversations for credible generalization assessment. Reset between topic sequences.

## Evaluation priorities

1. Does `SFです` yield a contextual reply, not another `どんな本` question?
2. Can the model develop conversation beyond the training topics (not just memorize specific examples)?
3. Is the v0.2.8 generic reply rate reduced on unseen samples?
4. Does character identity remain stable? Note `あなたは誰ですか` might be answered by rule-based persona router (`generation=0`), so it **cannot** alone verify learned persona preservation.
5. Are canonical CPU retrieval, unverified warning, unknown GPU blocking, Semantic Memory and `/sleep` preserved?

**Status:** Implementation committed; unit tests, GPU training, and dialogue-quality improvement require local execution.
