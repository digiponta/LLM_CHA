# LLM_CHA v0.7.34 — Wikipedia appended to Experimental LLM answers

The existing PENDING Candidate response is preserved, then a separate
**Wikipedia external/unverified** excerpt and source URL are appended.
This applies only to Experimental responses on the structured UNKNOWN
and explicit GATE_REVIEW paths that contain
`truth_state=EXPERIMENTAL_UNVERIFIED`.

It deliberately does not change Trusted answers, Wikipedia-only
fallback, raw corpus evidence, or Candidate Memory contents.
Ambiguous/missing Wikipedia hits do not overwrite the Experimental
answer. No automatic promotion, approval, or training from Wikipedia.
The GUI mirror presents the combined response on separate lines.

## PowerShell

```powershell
git fetch origin
git switch --track origin/v0.7.34
python -m unittest -v test_experimental_wiki_append_v0734.py test_gui_status_v0733.py
$env:LLM_CHA_MEMORY_FIRST="1"
$env:LLM_CHA_MEMORY_FIRST_MODE="constrained"
python chat_window_v061.py
```

Example format:

```text
AI> 【未承認・候補知識】（Experimental Candidate answer）
【Wikipedia検索結果・外部情報・未検証】（Article title）：（Excerpt）
出典：https://ja.wikipedia.org/wiki/...
[experimental_wiki_append=APPENDED, truth_state=EXTERNAL_UNVERIFIED, auto_promote=False]
```

Wikipedia lookup uses the existing 4-second-timeout acquisition
component. If lookup is unavailable, the original unapproved response
is retained. Additional fetches occur only for matching unapproved
Experimental Candidate answers, not every Trusted reply.
