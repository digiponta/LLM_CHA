# v0.2.33.45 — Context-Aware Clarification Policy

Adds a narrowly scoped, auditable preprocessing layer for polite Japanese clarification answers and explicit indirect topic changes. Negated and conflicting multi-option answers cannot silently become approved facts. No production Semantic Memory, checkpoint or /sleep is touched.

This addresses diagnostic errors already revealed in v0.2.33.44: `カーソルでお願いします`, `意味記憶のほうです`, `一旦ほかの話をしましょう`, `その前に違う件を聞きたい`.

**Important:** v0.2.33.44 cases have been observed and are now development data; matching them is regression improvement, **not** independent held-out generalization. Current classifier remains deterministic pattern matching, not learned contextual semantics.

### Run

```powershell
git fetch origin
git switch v0.2.33.45
git pull origin v0.2.33.45
python -m py_compile context_aware_clarification_v023345.py
python -m unittest -v test_context_aware_clarification_v023345.py test_clarification_robustness_v023344.py
python context_aware_clarification_v023345.py
```

Output: `results/context_aware_clarification_v023345.json` (refuses overwrite).

### Next experiment

Use newly labeled, previously unexamined utterances and multi-turn trajectories. Separate accidental clarification questions from necessary disambiguation, count turns-to-resolution and false acceptance. Explicit user confirmation remains a mandatory transition before a candidate is approved. The existing purpose DSS is real project code; referent resolution still relies on narrow rules and a shadow store.
