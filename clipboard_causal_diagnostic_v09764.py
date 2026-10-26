"""Read-only diagnostics for clipboard causal evidence routing."""
import re
from clipboard_causal_evidence_v09760 import INTENTS

def diagnose(question, source, topic):
    q = str(question or "").strip()
    text = str(source or "")
    matched = [(i, cues) for i, (p, cues) in enumerate(INTENTS) if p.search(q)]
    data = {"topic": topic or "-", "clipboard_chars": len(text),
            "intent_count": len(matched), "candidate_count": 0,
            "labeled_count": 0, "reason": "UNKNOWN"}
    if not topic:
        data["reason"] = "TOPIC_MISSING"
        return data
    if topic not in text[:650]:
        data["reason"] = "TOPIC_NOT_IN_SOURCE_HEAD"
        return data
    if not matched:
        data["reason"] = "INTENT_MISSING"
        return data
    index, cues = matched[0]
    label = "脆さとカットの難しさ" if index in (0,2) else "圧倒的な輝き"
    lines = [line.strip() for line in text.splitlines()]
    matches = [line for line in lines
               if 12 <= len(line) <= 480
               and any(cue in line for cue in cues)
               and re.search(r"(?:ため|により|ので|から)", line)]
    data["candidate_count"] = len(set(matches))
    data["labeled_count"] = len(set(line for line in matches if line.startswith(label+":") or line.startswith(label+"：")))
    data["reason"] = ("AMBIGUOUS_OR_MISSING_EVIDENCE"
                       if data["labeled_count"] != 1 else "MATCHED_CHECK_SUBJECT_GUARD")
    return data
