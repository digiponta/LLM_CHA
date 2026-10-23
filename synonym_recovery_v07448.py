"""v0.7.44.8: conservative source-preserving synonym recovery.

This module performs no knowledge promotion and writes no files.
"""
def recover_bare_synonym(user_text, lexicon, lookup, allowed):
    term = (user_text or "").strip()
    if not term or any(x in term for x in (" ", "\n", "?", "？", "とは")) or len(term) > 24 or term.startswith("/"):
        return None
    if not allowed(term):
        return None
    for synonym in lexicon.expand(term)[1:]:
        if synonym == term or not allowed(synonym):
            continue
        try:
            result = lookup(synonym)
        except (OSError, ValueError, KeyError, RuntimeError):
            continue
        if result and result.get("status") == "FOUND" and result.get("answer") and result.get("source"):
            return {"answer":result["answer"],"term":synonym,
                    "source":result["source"],"truth_state":"EXTERNAL_UNVERIFIED",
                    "train_ready":False,"auto_promote":False}
    return None
