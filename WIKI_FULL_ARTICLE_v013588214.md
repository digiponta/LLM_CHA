# LLM_CHA v0.13.58.82.14 — Wikipedia Full Article Evidence Retrieval

For GUI automatic Wikipedia fallback: when a topic article is found but its introductory excerpt contains no explicit requested attribute, fetch the matching full article's wikitext using the Japanese MediaWiki API and inspect plain Infobox assignments and narrowly formatted statements. Search results include source title and Wikipedia article URL, labeled EXTERNAL_UNVERIFIED. Does not change LLM weights, permanent Semantic Memory, or /sleep.

The first phase uses simple literal Infobox attributes, rejecting nested templates and markup. It cannot yet resolve complex Infobox templates, arbitrary prose, units/semantic ambiguity or Wikipedia redirects beyond what the API resolves. If no evidence is found, retains the distinct NO_ATTRIBUTE_EVIDENCE response. Search and network operations remain in the GUI's background worker.

Run on Windows:
```powershell
git fetch origin
git switch v0.13.58.82.14-wiki-full-article
python -m unittest -v test_wiki_full_article_v013588214.py test_wiki_topic_attribute_v013588213.py test_auto_wiki_unknown_v013588212.py
python chat_gui.py
```
Manual checks: `スファレライトの硬度は？`, `スファレライトの屈折率は？`, `量子力学とは？`, and a nonexistent term. A value found in Wikipedia must not be considered verified merely because it appears in an Infobox.
