"""v0.5.41 source-constrained conversational rendering for explicit /wiki retry.

No model-generation claims are added. The source excerpt is carried verbatim.
"""
def render(utterance, result, explicit=False):
    if not isinstance(result,dict) or result.get("status")!="EVIDENCE_FOUND":
        return result
    evidence=result.get("evidence_span")
    topic=result.get("topic")
    if not isinstance(evidence,str) or not evidence or not isinstance(topic,str):
        return result
    if not isinstance(utterance,str):utterance=""
    article_report=any(x in utterance for x in ("記事を読","ニュースを読","記事を見"))
    if not explicit and article_report and topic in utterance:
        intro=f"{topic}の記事を読んだのね。"
        ending="どんな内容が紹介されていた？"
        intent="ARTICLE_SHARING"
    else:
        intro=f"{topic}について確認したよ。"
        ending="気になった点があれば教えて。"
        intent="TOPIC_LOOKUP"
    return {**result,
            "answer":intro+"Wikipediaには「"+evidence.rstrip("。")+"。」と記載されている。"+ending,
            "route":"WIKIPEDIA_CONVERSATIONAL_REPAIR",
            "response_intent":intent,"evidence_preserved":True,
            "verified":False,"train_ready":False,"promoted":False}
