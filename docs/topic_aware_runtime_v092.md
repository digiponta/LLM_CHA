# LLM_CHA v0.9.2 — Topic-Aware Corpus Conversation Runtime

This branch integrates `topic_suggestion_v092.py` into the real `chat.py`
loop before unknown-fact handling for explicit topic requests.

The route `TOPIC_SUGGESTION_CORPUS` retrieves discussion themes from
`data/data-nagato.txt` and never marks these as verified scientific facts.
Definition questions like `量子力学とは` remain in the original QA/Wikipedia
path. It does not modify Semantic Memory or weights.

Windows PowerShell:
```powershell
git fetch origin
git switch --track origin/v0.9.2
python -m unittest -v test_topic_suggestion_v092.py test_corpus_answer_plan_v091.py
python chat.py
```
Suggested manual dialogue probes:
- `量子力学とは` — existing definition route preserved
- `量子力学的な話題は` — corpus-grounded topic suggestions
- `何か話題はありますか` — conversational topic suggestions
- `数学とは` and `文学とは` — existing QA route preserved

Limitations: current topic matching is intentionally narrow and heuristic.
This is not proof of LLM generation quality, topic-followup persistence,
correctness of physical interpretations, or independence from external data.
Runtime GPU smoke testing remains to be performed on Windows.
