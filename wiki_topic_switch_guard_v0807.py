"""v0.8.0.7: detect explicit topic switches before Wikipedia follow-up.

Do not clear context for elliptical follow-ups. This guard deliberately
recognizes only explicit Japanese noun-phrase requests.
"""
import re

PATTERNS=(
    re.compile(r"^(.{2,40}?)について(?:詳しく)?(?:教えて|説明して)(?:ください)?[？?！!。]*$"),
    re.compile(r"^(.{2,40}?)とは[？?。]*$"),
)
def explicit_topic(question):
    q=(question or "").strip()
    for pattern in PATTERNS:
        match=pattern.fullmatch(q)
        if match:
            return match.group(1).strip(" 、")
    return None

def should_reset_wiki_context(question,wiki_context):
    if not isinstance(wiki_context,dict):return False
    current=(wiki_context.get("title") or "").strip()
    requested=explicit_topic(question)
    if not requested or not current:return False
    # For different explicit terms, the previous article is not evidence.
    # Containment allows '量子ビットの基本単位' under '量子ビット'.
    return requested != current and current not in requested and requested not in current
