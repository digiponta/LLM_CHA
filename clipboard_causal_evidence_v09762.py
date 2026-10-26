"""Choose a source-explicit causal statement from noisy search-result text.

Prefer unique labeled evidence; do not treat repetition of a compatible
search snippet as a contradiction. Never infer or approve source claims.
"""
import re
from clipboard_causal_evidence_v09760 import INTENTS

LABELS = {
    "cut": ("脆さとカットの難しさ",),
    "fire": ("圧倒的な輝き",),
    "fragile": ("脆さとカットの難しさ",),
}

def retrieve(question, source, active_topic=None):
    q = str(question or "").strip()
    text = str(source or "")
    if not q or not text or not active_topic or q.startswith("/"):
        return None
    if active_topic not in text[:650]:
        return None
    explicit = re.match(r"^(.{2,55}?)の", q)
    if explicit and explicit.group(1).strip() != active_topic:
        return None
    matched = [(i, cues) for i, (pattern, cues) in enumerate(INTENTS) if pattern.search(q)]
    if not matched:
        return None
    index, cues = matched[0]
    label = ("脆さとカットの難しさ" if index in (0, 2) else "圧倒的な輝き")
    lines = [line.strip() for line in text.splitlines()]
    candidates = [line for line in lines
                  if 12 <= len(line) <= 480
                  and any(cue in line for cue in cues)
                  and re.search(r"(?:ため|により|ので|から)", line)]
    # A single explicitly labeled fact box outranks duplicated snippets.
    labeled = list(dict.fromkeys(line for line in candidates if line.startswith(label + ":") or line.startswith(label + "：")))
    if len(labeled) == 1:
        chosen = labeled[0]
    elif len(labeled) > 1:
        return None
    else:
        unique = list(dict.fromkeys(candidates))
        if len(unique) != 1:
            return None
        chosen = unique[0]
    return (f"コピーした資料には、{active_topic}について次の説明があります："
            f"「{chosen}」（クリップボード由来・未検証）")
