"""v0.7.44.15 guarded follow-up to unverified corpus evidence."""
FOLLOWUPS = frozenset(("もっと詳しく", "もう少し詳しく", "もっと詳しく教えて",
                       "もう少し詳しく教えて", "詳しく教えて", "詳しく"))

def corpus_followup(question, context):
    text=(question or "").strip().rstrip("。!?？")
    if text not in FOLLOWUPS or not context:
        return None
    subject=context.get("subject")
    if not subject or context.get("truth_state") != "UNVERIFIED":
        return None
    return {
        "answer": f"「{subject}」について、先ほど提示した原文は未検証の記述。追加で確認できる別の根拠がないため、これ以上は断定して説明できない。検証したい部分を指定して。",
        "route": "CORPUS_FOLLOWUP_NO_NEW_EVIDENCE",
        "truth_state": "UNVERIFIED",
        "train_ready": False,
        "auto_promote": False,
    }
