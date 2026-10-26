"""Conservative causal proposition retrieval from copied pages (v0.9.7.60).

Extracts a *source quote*, not a model-generated causal explanation.
No trust promotion, persistence or training.
"""
import re

INTENTS = (
    (re.compile(r"(?:なぜ|どうして|理由|原因).*(?:カット|加工)|(?:カット|加工).*(?:難しい|困難|理由|なぜ)"), ("カットの難しさ", "カットが", "加工やカット")),
    (re.compile(r"(?:なぜ|どうして|理由).*(?:虹色|輝|ファイア)|(?:虹色|輝き|ファイア).*(?:なぜ|理由)"), ("圧倒的な輝き", "分散度により", "ファイア")),
    (re.compile(r"(?:なぜ|どうして|理由).*(?:傷つき|脆い)|(?:傷つき|脆い).*(?:なぜ|理由)"), ("脆さとカットの難しさ", "モース硬度")),
)


def retrieve(question: str, source: str, active_topic: str | None = None) -> str | None:
    q = str(question or "").strip()
    text = str(source or "")
    if not q or not text or q.startswith("/") or not active_topic:
        return None
    if active_topic not in text[:650]:
        return None
    match = re.match(r"^(.{2,55}?)の", q)
    if match and match.group(1).strip() != active_topic:
        return None
    cues = next((words for pattern, words in INTENTS if pattern.search(q)), None)
    if cues is None:
        return None
    candidates = []
    for line in text.splitlines():
        line = line.strip()
        if not 12 <= len(line) <= 480:
            continue
        if not any(cue in line for cue in cues):
            continue
        if not re.search(r"(?:ため|により|ので|から)", line):
            continue
        # Require an explicit causal connector in the same source line.
        if line not in candidates:
            candidates.append(line)
    if len(candidates) != 1:
        return None
    return (f"コピーした資料には、{active_topic}について次の説明があります："
            f"「{candidates[0]}」（クリップボード由来・未検証）")
