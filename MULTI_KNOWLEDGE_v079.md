# LLM_CHA v0.7.9 — Multi-Knowledge Generalization & Retention

Four **fictional** experiment-only question-answer facts are registered as
PENDING in a newly isolated Candidate Memory, with eight paraphrase holdout
questions (two per fact). No factual claims about the real world are implied.

Two separate adapters are trained from the same frozen Base checkpoint:
- Rank 16, Epoch 30, LR 1e-3
- Rank 32, Epoch 30, LR 1e-3

The benchmark compares greedy free-generation exact match for Base / Trusted
control / Experimental, including **per-fact** scores.

## Windows

```powershell
git fetch origin
git switch --track origin/v0.7.9
python -m unittest -v test_multi_knowledge_v079.py test_generalization_v078.py
python run_multi_knowledge_v079.py --output-dir results/multi_knowledge_v079
```

Files are under `results/multi_knowledge_v079/`:
`dataset/candidates.jsonl`, `dataset/holdouts.json`,
`r16_e30/experimental-adapter.pt`,
`r32_e30/experimental-adapter.pt`,
`paraphrase_raw.json`, `summary_v079.json`.

## Retention probes (optional)

Create a *separately verified* JSON file, **not** an Approved Memory
promotion, with entries of the form:

```json
[
  {"question":"verified question from an existing QA suite",
   "reference":"its independently verified canonical answer"}
]
```

Then run a **fresh** experiment directory with:

```powershell
python run_multi_knowledge_v079.py `
  --protected-qa data/my_verified_protected_qa.json `
  --output-dir results/multi_knowledge_v079_protected
```

The tool compares exact-match Base vs Experimental on this optional set.
Because it cannot authenticate the source or review process, such rows remain
user-supplied probes, not automatically approved knowledge. The
`verified_protected_probes` count stays zero and `quality_pass` remains
null. Without any supplied probes retention is **not evaluated**.

## Research interpretation

- Holdout questions differ from the training questions, but their *answers*
  are included in training. This tests paraphrase transfer, not factual
  generalization to unknown knowledge.
- Four facts and eight test questions are exploratory, not statistically
  sufficient. No independent held-out facts or data-leakage audit yet.
- No automatic promotion, Trusted Adapter training, or production `chat.py`
  integration occurs.
