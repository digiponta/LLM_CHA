# LLM_CHA v0.7.36 — Wikipedia Lead Quality and GUI Source Visibility

## Changes
- New `wiki_lead_v0736.py`: select a complete sentence from the
  article excerpt, avoiding sentence breaks inside Japanese/ASCII
  parentheses; cap displayed excerpt at 240 characters.
- Malformed incomplete article introductions such as
  `空間（…）とは、。` no longer render as valid summaries.
  When no suitable excerpt is available, retain the original local
  unverified evidence only.
- Updated `experimental_wiki_append_v0734.py` (also used by
  `raw_wiki_parallel_v0735.py`) to use the lead extractor.
- GUI mirror: local raw corpus excerpts are rendered in a distinct
  text color, Wikipedia excerpts and URLs in another color.
- All knowledge remains unverified; no automatic promotion or training.

## Windows PowerShell

```powershell
git fetch origin
git switch --track origin/v0.7.36
python -m unittest -v test_wiki_lead_v0736.py test_raw_wiki_parallel_v0735.py test_experimental_wiki_append_v0734.py
$env:LLM_CHA_MEMORY_FIRST="1"
$env:LLM_CHA_MEMORY_FIRST_MODE="constrained"
python chat_window_v061.py
```

Prompts: `時間`, `空間`, `宇宙`, `セル画`.
Wikipedia search may fail or return insufficient source material;
this never changes the original source-derived answer.

Note: This release implements *presentation distinction*, not
semantic agreement/disagreement detection between sources.
