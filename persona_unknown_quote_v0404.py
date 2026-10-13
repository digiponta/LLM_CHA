"""v0.4.4: conservative UNKNOWN persona quote candidate (read-only).

A literal mention is NOT a definition or scientific verification.
"""
from pathlib import Path
from persona_routing_v0374 import ranked_persona_reply

def unknown_persona_quote(source: str | Path, question: str, focus: str):
    focus=(focus or "").strip()
    query=(question or "").strip().rstrip("。？！!? ")
    if not focus or len(focus)>100 or query not in (focus+"とは",focus+"とは何ですか",focus+"について教えて"):
        return None
    _,rows=ranked_persona_reply(source,focus,limit=2)
    if not rows:
        return None
    return {
        "answer": "この人格の原文には「"+focus+"」に関連する記述がありますが、"
                  "その定義として検証された内容ではありません。"+ "".join(
                      "\n・「"+row.excerpt+"」" for row in rows),
        "focus":focus,"source_lines":[row.line for row in rows],
        "evidence_ids":[row.id for row in rows],
        "mode":"RELATED_LITERAL_QUOTE_NOT_DEFINITION",
        "factual_truth":"NOT_ASSESSED"
    }
