"""v0.5.7 conservative topic grounding for conversational generations.

Lexical/closed-vocabulary signal only; never promotes facts or marks an answer
KNOWN. Focused on movie-domain dialogue regression observed in the runtime.
"""
import re

TOPICS={"映画":("映画","アベンジャーズ","作品","監督","俳優","シーン","上映","観た","観る","鑑賞","ストーリー","映画館","マーベル"),
        "音楽":("音楽","楽曲","歌","曲","歌手","バンド","演奏","ライブ")}
CONTINUATIONS=("続きの話","続きを話","さっきの話","その話を続け","もっと話そう")
def topic_for(text):
    for label,terms in TOPICS.items():
        if any(word in text for word in terms):return label
    return None

def resolve_context(user_text,prior_topic):
    if prior_topic and any(x in user_text for x in CONTINUATIONS):
        return prior_topic+"の話の続きをしましょう。"
    return user_text

def grounded(question,answer,prior_topic=None):
    topic=topic_for(question) or prior_topic if any(t in question for t in CONTINUATIONS) else topic_for(question)
    if not topic:return True,"topic unclassified"
    if not answer or len(answer.strip())<2:return False,"empty topic response"
    terms=TOPICS[topic]
    if any(word in answer for word in terms):return True,"topic anchor present"
    if topic=="映画" and any(word in answer for word in ("どんな","何が好き","おすすめ","好きですか","教えて","そうなんですね","なるほど","いいですね")):
        return True,"conversational response (limited heuristic)"
    return False,"topic grounding absent: "+topic
