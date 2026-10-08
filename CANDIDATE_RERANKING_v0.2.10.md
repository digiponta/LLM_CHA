# LLM_CHA v0.2.10 — Candidate Reranking Pilot

Branch `v0.2.10`, based on `v0.2.9`. Model weights, Semantic Memory, Truth-State, and `/sleep` are unchanged.

## Change

Previously the greedy candidate was always the primary answer, while the other `--probe-count` results were used only for gate agreement. When `--candidate-reranking` is enabled (default) for non-factual character conversations, the existing generated candidates are scored before the existing semantic/unknown/quality gates.

Scoring penalizes generic fillers and repeated previous assistant questions; a minimum confidence/margin filter excludes locally implausible candidates, and a slight length benefit rewards nontrivial replies. The original candidate wins equal scores. All candidates still flow through the existing unknown-gate agreement logic, and the selected candidate receives the same semantic and dialogue checks. **The reranker does not independently certify truth or answer quality.**

This is a heuristic and diagnostic stage, **not additional model training or generation**. Alternative probes can be noisier than greedy, so compare both settings before considering the default stable. The module does not use canonical factual answers to pick new factual assertions.

## Run

```powershell
git fetch origin
git switch --track origin/v0.2.10
python -m unittest -v test_candidate_reranker_v0210.py test_dialogue_state_v029.py test_conversation_quality_v027.py test_conversation_context_v025.py
python chat.py --model model/model-llm-cha-quality-v028.pt --tokenizer ..\LLM_TRY\model\tokenizer-v0.7-bpe.json --character nagato --dialogue-history-turns 2 --probe-count 3 --temperature 0 --show-context --show-dialogue-state --show-conversation-diagnostics --show-candidate-ranking
```

Conversation: `最近、小説にはまっています`, `SFです`, `その話、続けて`, `/reset`, `CPUとは`. Compare A/B by repeating with `--no-candidate-reranking`, all else unchanged.

**Important:** The candidate score is not a calibrated probability. Reranking can change the probe agreement statistics because the primary candidate is changed, although the candidate set is preserved. A reranked answer is *still rejected* if the downstream gates do not accept it. When no eligible candidate exists, the original greedy candidate remains the primary and standard gates handle the rejection.

Current status: Code and tests committed. User-side Python unit tests and GPU inference remain to be run before claiming improvements.
