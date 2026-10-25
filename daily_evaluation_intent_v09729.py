"""v0.9.7.29 — bounded daily evaluation acknowledgements.

Only recognize explicit, short user-reported assessments during an active
clipboard experience. No general-purpose emotion inference or promotion.
"""
RESPONSES={
 "POSITIVE":("それは良かったね。",("満足","満足した","とても満足した","満足だった","よかった","良かった","美味しかった","おいしかった","楽しかった","気に入った")),
 "DISAPPOINTMENT":("それは残念だったね。",("期待外れだった","美味しくなかった","おいしくなかった","がっかりした","残念だった","残念でした")),
 "SADNESS":("それは悲しかったね。",("悲しかった","寂しかった","つらかった")),
}
def classify_evaluation(utterance):
    q=str(utterance or "").strip().rstrip("。！？!? ")
    for label,(reply,phrases) in RESPONSES.items():
        if q in phrases:return {"label":label,"response":reply,"utterance":q}
    return None
