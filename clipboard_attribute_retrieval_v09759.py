"""Read-only attribute retrieval from user-copied text (v0.9.7.59).

Scope: explicit key:value fact lines, no inference or model training.
"""
import re

ATTRIBUTES = {
    "硬度": ("モース硬度", "硬度"),
    "屈折率": ("屈折率",),
    "産地": ("主な産地", "産地"),
    "化学組成": ("化学組成", "組成"),
    "分散度": ("分散度",),
}
QUESTION_ATTR = {
    "硬度": ("硬度", "モース硬度"),
    "屈折率": ("屈折率",),
    "産地": ("産地", "どこで採", "どこで産"),
    "化学組成": ("化学組成", "成分", "組成"),
    "分散度": ("分散度",),
}


def retrieve(question, source, active_topic=None):
    q = str(question or "").strip()
    text = str(source or "")
    if not q or not text or q.startswith("/"):
        return None
    explicit = re.match(r"^(.{2,55}?)の(?:モース硬度|硬度|屈折率|主な産地|産地|化学組成|成分|分散度)", q)
    topic = explicit.group(1).strip() if explicit else active_topic
    if not topic:
        return None
    # Avoid applying a copied page to an unrelated topic.
    if topic not in text[:650]:
        return None
    # A short follow-up must use an already resolved topic.
    attr = next((name for name, variants in QUESTION_ATTR.items()
                 if any(word in q for word in variants)), None)
    if attr is None:
        return None
    # Keep this extractor strictly to fact lines, with length and
    # conflicting-value checks; unstructured reasoning is delegated elsewhere.
    found = []
    for line in text.splitlines():
        line = line.strip()
        if not line or len(line) > 260:
            continue
        for label in ATTRIBUTES[attr]:
            m = re.match(r"^" + re.escape(label) + r"\s*[:：]\s*(.+)$", line)
            if m:
                value = m.group(1).strip().rstrip("。 ")
                if value and len(value) <= 160 and value not in found:
                    found.append(value)
    if len(found) != 1:
        return None
    return f"コピーした資料では、{topic}の{attr}は{found[0]}と記載されています。（クリップボード由来・未検証）"
