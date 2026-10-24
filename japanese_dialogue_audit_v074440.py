"""v0.7.44.40: offline Japanese conversation anomaly audit."""
IDENTITY={"長門有希。","長門有希"}
FOLLOWUPS={"もっと詳しく","もう少し詳しく","詳しく","その続き"}
def audit(question,answer,topic=None):
    q=(question or "").strip()
    a=(answer or "").strip()
    flags=[]
    if not a: flags.append("EMPTY")
    if a in IDENTITY and q not in ("あなたは誰","あなたは誰ですか","名前は"):
        flags.append("UNRELATED_IDENTITY")
    if q in FOLLOWUPS and topic and a in IDENTITY:
        flags.append("TOPIC_LOST")
    if "回答をうまく生成できませんでした" in a:
        flags.append("GENERATION_FAILURE")
    return {"question":q,"answer":a,"topic":topic,"flags":flags,"review":bool(flags)}
def audit_dialogue(turns):
    topic=None
    records=[]
    for turn in turns:
        q=turn.get("question","")
        if "とは" in q: topic=q.split("とは",1)[0].strip() or None
        records.append(audit(q,turn.get("answer",""),topic))
    return {"total":len(records),"flagged":sum(r["review"] for r in records),"records":records}
