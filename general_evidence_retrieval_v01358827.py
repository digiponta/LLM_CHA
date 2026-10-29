"""Conservative extractive retrieval for menu/food queries from session evidence.

Returns exact source lines, never generates products. Does not treat "search opened"
as evidence. In absence of matching source, returns a diagnostic instead of guessing.
"""
import re

FOOD = re.compile(r"フード|食べ物|サンドイッチ|パン|ケーキ|スコーン|ドーナツ|ペストリー|ベーカリー|焼き菓子|デザート|軽食|クッキー|マフィン")
MENU = re.compile(r"メニュー|商品一覧|ドリンク|フード|コーヒー|ラテ|フラペチーノ|ティー|サンドイッチ|ケーキ|スコーン|ペストリー")
QUESTION = re.compile(r"メニュー|フード|食べ物|飲み物|商品|ドリンク")
STOP = re.compile(r"^(?:AI Mode|All|Shopping|Images|Videos|More|Tools|ニュース|News|Skip to|Translate this|Sponsored|スポンサー|People also ask|Ask anything|Read more|https?://|www\\.)", re.I)

def is_general_question(question):
    return bool(QUESTION.search(question or ""))

def relevant_lines(text, question, topic, limit=4):
    pattern=FOOD if re.search(r"フード|食べ物",question) else MENU
    lines=[x.strip().lstrip("•・*- ") for x in text.splitlines()]
    lines=[x for x in lines if 4<=len(x)<=220 and not STOP.search(x)]
    # Explicit, category-qualified content; bare navigation headings are insufficient.
    matches=[]
    for line in lines:
        if not pattern.search(line):continue
        if line in ("フード","ドリンク","メニュー","商品一覧"):continue
        if re.fullmatch(r"(?i)[\w\s|/・、]+",line) and len(line)<20:continue
        if re.search(r"(メニュー|フード|ドリンク|食べ物|商品一覧)\s*[：:]",line) or (
            len(line)>18 and re.search(r"サンドイッチ|ケーキ|スコーン|ドーナツ|ラテ|フラペチーノ|マフィン|クッキー|パン|ペストリー",line)
        ):
            matches.append(line)
    unique=list(dict.fromkeys(matches))
    return unique[:limit]

def retrieve(store, question):
    if not is_general_question(question) or not store.topic:
        return None
    candidate_records=[r for r in reversed(store.records) if r["topic"]==store.topic]
    if not candidate_records:
        return {"status":"NO_EVIDENCE","topic":store.topic}
    for record in candidate_records:
        text=record["text"]
        if store.topic.lower() not in text.lower():
            continue
        quotes=relevant_lines(text,question,store.topic)
        if quotes:
            return {"status":"EXCERPTS","topic":store.topic,"source":record["source"],
                    "source_title":record.get("source_title",record["source"]),
                    "quotes":quotes,"truth_state":"EXTERNAL_UNVERIFIED"}
    return {"status":"NO_MATCH","topic":store.topic}
