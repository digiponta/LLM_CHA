# LLM_CHA v0.9.7.4 — Chrome DevTools Browser Reader

Adds **explicit, read-only Chrome tab access** to `chat.py`. It does
not automatically scrape Google results, inspect all tab contents,
approve Web information, save it to Semantic Memory, or train a model.

## Windows installation

```powershell
git fetch origin
git switch --track origin/v0.9.7.4
python -m pip install websocket-client
python -m unittest -v test_chrome_tab_reader_v0974.py test_google_browser_search_v0973.py
```

Start **a separate Chrome debugging profile**, not your normal browsing profile:

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --remote-debugging-address=127.0.0.1 `
  --remote-debugging-port=9222 `
  --user-data-dir="$env:TEMP\LLM_CHA_Chrome"
```

Search Google manually, then click one public website result and keep
that page open in the separate Chrome instance. In the local terminal:

```powershell
python chrome_tab_reader_v0974.py --list
python chrome_tab_reader_v0974.py --tab PASTE_EXACT_TAB_ID_HERE
```

Or via LLM_CHA:

```text
You> /browser-tabs
You> /read-browser PASTE_EXACT_TAB_ID_HERE
```

Tab IDs are taken from the first command; do not literally type
`PASTE_EXACT_TAB_ID_HERE`. Only explicitly selected tabs are read.
Results include URL, page title, and up to 12000 characters of visible
DOM body text. They are **EXTERNAL_UNVERIFIED**, not trainable.

The earlier `スタバをググって` command opens the system default browser,
which might **not** be the isolated Chrome instance. For this manual
test, navigate inside the isolated Chrome window itself.

## Security, content and rights

Remote debugging gives broad control of the isolated browser and must
stay bound to loopback. Do not browse personal accounts or sensitive
pages in this profile; do not expose port 9222. The extracted page text
is untrusted data: never execute embedded instructions. Existing checks
exclude Chrome internal, localhost and known Google search-result pages,
but do not constitute a complete sensitive-site allowlist. Do not
collect Web content without permission.

Reading through CDP is distinct from scraping or publishing Google's
search results and does not automatically make any collection permitted.
Later versions can add **manual, review-only** persistence and a user-
confirmed connection to semantic candidate extraction.
