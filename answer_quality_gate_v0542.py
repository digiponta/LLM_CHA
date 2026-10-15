"""v0.5.42 read-only Answer Quality Gate suggesting explicit /wiki.

Does not change model acceptance, truth state, or perform network operations.
"""
def evaluate(utterance, reply, *, accepted, agreement=None, resolution=None,
             wiki_topic=None, weak_agreement=0.35):
    base={"suggest_wiki":False,"diagnostic_only":True,"train_ready":False,
          "auto_lookup":False,"auto_promote":False}
    if not isinstance(utterance,str) or not utterance.strip():
        return {**base,"status":"NO_USER_CONTEXT","reason":"EMPTY_UTTERANCE"}
    if not wiki_topic:
        return {**base,"status":"NO_WIKI_TOPIC","reason":"TOPIC_UNAVAILABLE"}
    if not accepted or reply in ("未学習です","(no response)",""):
        return {**base,"status":"REVIEW","reason":"UNKNOWN_OR_REJECTED","suggest_wiki":True}
    if isinstance(agreement,(int,float)) and agreement<weak_agreement:
        return {**base,"status":"REVIEW","reason":"LOW_PROBE_AGREEMENT","suggest_wiki":True}
    return {**base,"status":"ACCEPT","reason":"NO_TRIGGER_DETECTED"}
