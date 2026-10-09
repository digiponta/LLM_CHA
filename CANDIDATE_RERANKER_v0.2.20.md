# LLM_CHA v0.2.20 — Context-Aware Candidate Reranker

Without retraining model weights, this experiment replaces v0.2.10 pre-gate ranking with `candidate_reranker_v0220.py`. It downranks very short acknowledgments, rewards modest topic overlap with the latest user question and accepted-history user turns, checks existing minimum generation confidence and repetition, and preserves greedy ties.

**Important:** This does not fabricate content. If all candidates are superficial, the model may still answer `そう。` or fail the existing quality gate. The old semantic/unknown/truth gates remain authoritative, so a well-ranked candidate can still be rejected.

## PowerShell
```powershell
git fetch origin
git switch --track origin/v0.2.20
python -m unittest -v test_candidate_reranker_v0220.py test_conversation_gate_v0219.py test_conversation_runtime_wiring_v0219.py
python chat.py --model model/model-llm-cha-foundation-dialogue-v0218.pt --tokenizer ../LLM_TRY/model/tokenizer-v0.7-bpe.json --dialogue-history-turns 2 --show-candidate-ranking --show-context
```

Try `こんにちは` → `最近、SF小説を読んでいます` → `その話を続けて` → `長門有希について教えて`. Review candidate entries and actual selected answers; improvement in ranking alone is insufficient. Compare quality with v0.2.19 on the same inputs and seeds before release.

No GPU inference tests have been run remotely.
