#!/usr/bin/env python3
"""Stable natural-language references for LLM_CHA candidate semantic data.

References are local, versioned and content-addressed. They are NOT externally
resolvable URLs. Evidence remains unverified and never promotes itself.
"""
import hashlib
from copy import deepcopy
from urllib.parse import quote

VERSION = "v0.6.3"
PREFIX = "nl://"


def _digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _ref(conversation_id, turn, text, language):
    checksum = _digest(text)
    text_id = f"TXT-{checksum[:24]}"
    uri = f"{PREFIX}{quote(conversation_id, safe='')}/{turn}/{text_id}"
    return {
        "text_id": text_id, "language": language, "relation": "source",
        "uri": uri, "version": 1, "content_hash": f"sha256:{checksum}"
    }


def attach_natural_language_refs(memory, language="ja"):
    """Add references to candidate propositions, keeping full immutable evidence.

    Idempotent for legacy and upgraded records. Does not infer equivalence,
    translation, or factual truth. Fails closed on malformed provenance.
    """
    if not isinstance(language, str) or not language.strip():
        raise ValueError("language required")
    conversation_id = memory.get("conversation_id")
    if not isinstance(conversation_id, str) or not conversation_id:
        raise ValueError("conversation_id required")
    staged = deepcopy(memory)
    store = staged.setdefault("natural_language_texts", {})
    if not isinstance(store, dict):
        raise ValueError("invalid text store")
    last_turn = staged.get("last_turn", 0)
    for prop in staged.get("propositions", []):
        turn = prop.get("source_turn")
        source = prop.get("source_text")
        if (not isinstance(turn, int) or isinstance(turn, bool)
                or not 1 <= turn <= last_turn
                or not isinstance(source, str) or not source.strip()):
            raise ValueError("invalid semantic evidence")
        ref = _ref(conversation_id, turn, source, language)
        existing = store.get(ref["uri"])
        entry = {
            "text_id": ref["text_id"], "language": language, "text": source,
            "source_turn": turn, "version": 1,
            "content_hash": ref["content_hash"]
        }
        if existing is not None and existing != entry:
            raise ValueError("natural-language reference conflict")
        store[ref["uri"]] = entry
        refs = prop.setdefault("natural_language_refs", [])
        if not isinstance(refs, list):
            raise ValueError("invalid natural_language_refs")
        if refs and ref not in refs:
            raise ValueError("existing reference differs from evidence")
        if not refs:
            refs.append(ref)
    staged["natural_language_refs_version"] = VERSION
    memory.clear()
    memory.update(staged)
    return memory


def resolve_natural_language(memory, uri):
    if not isinstance(uri, str) or not uri.startswith(PREFIX):
        raise ValueError("unsupported natural-language URI")
    entry = memory.get("natural_language_texts", {}).get(uri)
    if not isinstance(entry, dict):
        raise KeyError(uri)
    text = entry.get("text")
    if not isinstance(text, str) or entry.get("content_hash") != f"sha256:{_digest(text)}":
        raise ValueError("text integrity failure")
    if entry.get("version") != 1:
        raise ValueError("unsupported text version")
    return text
