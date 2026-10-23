# LLM_CHA v0.7.35 — Unverified Source and Wikipedia in One Answer

For **RAW_CONCEPT_EVIDENCE**, and **CORPUS_MEMORY** only when its
truth state is `UNVERIFIED`, show the original source-derived
unverified answer followed by a clearly labeled Wikipedia extract and
article URL in the same answer (stacked sections in the conversation
GUI). The output order is local source first, external reference
second. Wikipedia never overwrites original text.

The existing `experimental_wiki_append_v0734.py` formatting and
Wikipedia lookup component are reused. Ambiguous, missing, invalid, and
failed lookups leave the source-derived answer unchanged. The data
remain unverified; the operation neither verifies claims nor promotes
Candidate knowledge. Trusted/Approved responses and identity replies
are unaffected.

## PowerShell

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch --track origin/v0.7.35
python -m unittest -v test_raw_wiki_parallel_v0735.py test_experimental_wiki_append_v0734.py
$env:LLM_CHA_MEMORY_FIRST="1"
$env:LLM_CHA_MEMORY_FIRST_MODE="constrained"
python chat_window_v061.py
```

Test prompts: `時間`, `空間`, `宇宙`. Where an unambiguous
Wikipedia article is found, an external reference appears beneath the
corpus quote. `長門` and `貴方の名前は` keep their existing paths.

This release affects runtime answer display only and does not retrain
either LLM. The GUI mirrors multiline responses with the existing
conversation parser. The experiment can be audited from
`[raw_wiki_parallel=APPENDED,...]` logs.
