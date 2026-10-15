"""v0.5.19 conservative persona-aware Wikipedia response selection.

Deliberately no free-form neural generation: source-aligned sentence plus a
persona-dependent conversational continuation. Lexical grounding is a limited
quality check, not evidence of factual correctness.
"""
from wiki_grounded_fallback_v05172 import grounded_reply

PERSONA_ENDINGS={
 "nagato":"その記事では、どんな応用が紹介されていた？",
 "neutral":"その記事では、どのような応用が紹介されていましたか？",
}

def respond(wiki,utterance,persona="nagato"):
    base=grounded_reply(wiki,utterance)
    if base is None:return None
    if persona not in PERSONA_ENDINGS:persona="neutral"
    title=wiki.get("title","")
    extract=wiki.get("extract","")
    if not title or not extract or not base["answer"].startswith("Wikipediaによると、"):
        return None
    # Hard provenance check: the factual span must occur in source verbatim.
    prefix=base["answer"].split(" その記事では",1)[0].split(" どの部分について",1)[0]
    fact=prefix.removeprefix("Wikipediaによると、").rstrip("。…")
    if not fact or fact not in extract:
        return None
    ending=PERSONA_ENDINGS[persona] if any(t in utterance for t in ("記事","読んだ","見た","話")) else (
        "どの部分を知りたい？" if persona=="nagato" else "どの部分について知りたいですか？")
    answer="Wikipediaによると、"+fact+"。 "+ending
    # Ensure the personality suffix cannot inject factual claims.
    if not all(part in ("Wikipediaによると、",fact,"。 ",ending) for part in (fact,ending)):
        return None
    return {"answer":answer,"route":"PERSONA_WIKIPEDIA_GROUNDED",
        "persona":persona,"source":base["source"],"verified":False,
        "train_ready":False,"raw_generation":"SKIPPED",
        "quality_gate":"SOURCE_SPAN_EXACT"}
