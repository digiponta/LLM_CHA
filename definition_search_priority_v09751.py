"""v0.9.7.51 routing priorities for explicit definition/search queries."""

def is_definition_query(text):
    s=str(text or "").strip()
    return bool(s and "とは" in s and not s.startswith("/"))

def clipboard_allowed(text):
    return not is_definition_query(text)

def daily_allowed(text):
    return not is_definition_query(text)
