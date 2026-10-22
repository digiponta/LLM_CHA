#!/usr/bin/env python3
"""Opt-in Aozora book/author lookup based on provenance-bearing JSONL.
Literary corpus is evidence, NOT approved factual memory.
"""
import hashlib
import json
import re
from pathlib import Path

WORKS = {
    "789": {"title":"吾輩は猫である","author":"夏目漱石","aliases":["吾輩は猫である","吾輩"]},
    "1567": {"title":"走れメロス","author":"太宰治","aliases":["走れメロス"]},
}

def load_catalog(path):
    found = {}
    source = Path(path)
    if not source.is_file():
        return {}
    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(),1):
        if not line.strip():
            continue
        row = json.loads(line)
        provenance = row.get("provenance") or {}
        key = str(provenance.get("work_id",""))
        if key not in WORKS:
            continue
        txt = row.get("text")
        refs = row.get("natural_language_refs") or []
        if not isinstance(txt,str) or not refs:
            raise ValueError(f"missing Aozora source evidence at row {number}")
        digest = "sha256:" + hashlib.sha256(txt.encode("utf-8")).hexdigest()
        if refs[0].get("content_hash") != digest:
            raise ValueError(f"corrupted Aozora source at row {number}")
        if (provenance.get("title") != WORKS[key]["title"] or
                provenance.get("author") != WORKS[key]["author"]):
            raise ValueError(f"untrusted Aozora metadata at row {number}")
        found.setdefault(key, []).append(row)
    return found

def route_literature(text, catalog):
    """Return (answer, metadata) or None; slash commands never intercepted."""
    text = text.strip()
    if not text or text.startswith("/"):
        return None
    # Deliberately refuse to guess whether a generic cat question concerns a novel.
    if re.fullmatch(r"猫(?:は|って|とは|について)?[？?]?",text):
        return ("猫についての一般的な質問ですか。それとも夏目漱石の『吾輩は猫である』についてですか？",
                {"route":"AOZORA_CLARIFY","train_ready":False})
    candidate = []
    for key,work in WORKS.items():
        if key not in catalog:
            continue
        if any(alias in text for alias in work["aliases"]):
            candidate.append(key)
    if len(candidate) != 1:
        return None
    key = candidate[0]
    work = WORKS[key]
    first = catalog[key][0]
    source = first["provenance"]
    answer = f"『{work['title']}』は{work['author']}の作品。青空文庫の本文を参照できる。どの部分を知りたい？"
    metadata = {"route":"AOZORA_LITERATURE","work_id":key,
                "source":source["card_url"],"text_ref":first["natural_language_refs"][0]["uri"],
                "truth_state":"EXTERNAL_UNVERIFIED","train_ready":False,"promoted":False}
    return answer, metadata
