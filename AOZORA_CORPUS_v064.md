# 青空文庫 → LLM_CHA 学習準備 (v0.6.4)

This tool makes a **rights-reviewed corpus for training preparation**, not an
automated model fine-tuning command. It does not update weights, Semantic
Memory or `/sleep`. It does not crawl the entire website.

## Input: reviewed works

Prepare `data/aozora_manifest.json` manually, for example:

```json
[
  {
    "work_id": "12345",
    "title": "作品名",
    "author": "著者名",
    "card_url": "https://www.aozora.gr.jp/cards/000001/card12345.html",
    "zip_url": "https://www.aozora.gr.jp/cards/000001/files/12345_example.zip",
    "rights_checked": true,
    "rights_basis": "public_domain"
  }
]
```

**The above entry is a format example only; the IDs and URLs are not
verified.** Replace them with exact information from each work's Aozora
catalog card. Set `rights_checked=true` only after checking **both**
author and any translator rights, and relevant conditions. This first
version accepts only verified public-domain works, not all of Aozora Bunko.

Official guidelines: https://www.aozora.gr.jp/guide/kijyunn.html

## Run (Windows PowerShell)

```powershell
git fetch origin
git switch v0.6.4
git pull --ff-only origin v0.6.4
python -m unittest -v test_prepare_aozora_corpus_v064.py
python prepare_aozora_corpus_v064.py --manifest data/aozora_manifest.json --max-works 5 --output data/aozora_v064
```

Output:
- `data/aozora_v064/raw/<work_id>.txt` — original decoded text for audit.
- `data/aozora_v064/aozora_train.txt` — plain UTF-8 learning text for a separately configured language-model training run.\n- `data/aozora_v064/aozora_semantic_corpus.jsonl` — cleaned chunks
  containing author/title/source links, SHA-256 source checksum and
  `natural_language_refs`.

Review the JSONL; use the TXT as input for a **separately configured and evaluated**
fine-tuning pipeline. Do not feed it directly into personal-fact
Semantic Memory or truth-promote fictional statements. Narrative literature
requires train/eval splitting by **work**, not random chunk, to avoid leakage.

## Current scope / limitations

- `nl://` URIs are corpus-local logical identifiers; no remote URI resolver
  and no cross-LLM SKI synchronization is included.
- Ruby and annotation cleanup is intentionally conservative and may
  need per-work review. It is not a complete Aozora markup parser.
- ZIP must contain exactly one `.txt` file and respect size limits.
- No automatic catalog discovery, rights inference, GPU training,
  automatic `/sleep`, or quality claims.
- Please rate-limit requests and cache successful downloads. The tool
  defaults to a 2-second interval between works.
