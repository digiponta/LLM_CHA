# LLM_CHA v0.6.15 — Non-subject evidence retrieval

User requirement: concepts mentioned *inside* a sentence in data-nagato.txt
should be retrievable even if they were not stored as a subject.

Lookup order:
1. Explicit Subject index retrieval; respect the existing Truth Gate.
2. **Only on Subject miss**, scan raw Nagato corpus for sentence fragments
   containing the focus term. Show up to three fragments with
   `【原文中の関連記述・未検証】` marker.
3. If neither supplies evidence, continue existing unknown/Wikipedia route.

Raw evidence is displayed as corpus **quotes**, not verified factual claims.
It is not added to semantic knowledge, /sleep, SKI, or a training queue.
Metadata includes local provenance and `truth_state=UNVERIFIED`.

```powershell
git fetch origin
git switch --track origin/v0.6.15
python -m unittest -v test_raw_concept_evidence_v0615.py
python chat_window_v061.py --latest-experimental
```

Test inputs: `時間`, `時空間`, `宇宙`.
Known indexed Subject results still take precedence. This is a lexical
candidate search, not a semantic entailment or verification engine.
