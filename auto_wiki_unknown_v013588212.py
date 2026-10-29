"""Wikipedia fallback for UNKNOWN responses. Network requests are never on the GUI thread."""
import json
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

UNKNOWN_MARKER = re.compile(r"^(?:未学習です[。．.]?|未学習|わかりません[。．.]?)$")
QUESTION_PREFIX = re.compile(r"^(?:教えて|説明して|詳しく教えて)\s*")
QUESTION_SUFFIX = re.compile(r"(?:とは|について(?:教えて|説明して)?|って(?:何|なに)|は(?:何|なに)|を教えて|について知りたい|の意味は)[？?。．.]*$")
STOP_WORDS = {"これ", "それ", "あれ", "何", "なに", "誰", "どこ", "いつ", "どうして", "なぜ"}
MAX_RESULTS = 3

def is_unknown_answer(answer):
    return bool(UNKNOWN_MARKER.fullmatch((answer or "").strip()))

def search_term(question, active_topic=""):
    q=(question or "").strip().rstrip("？?。．.")
    q=QUESTION_PREFIX.sub("",q)
    q=QUESTION_SUFFIX.sub("",q).strip(" のはを")
    if not q or q in STOP_WORDS or len(q)>60:
        return active_topic.strip()
    if len(q)<=3 and active_topic and re.search(r"^(?:意味|特徴|成分|用途|産地|性質|硬度|屈折率)",q):
        return active_topic.strip()
    return q

def search_wikipedia(query, opener=urlopen):
    if not query:
        return {"status":"NO_HIT","hits":[]}
    params=urlencode({"action":"query","generator":"search","gsrsearch":query,
                      "gsrlimit":5,"prop":"extracts","exintro":"1",
                      "explaintext":"1","exchars":550,"format":"json"})
    api="https://ja.wikipedia.org/w/api.php?"+params
    req=Request(api,headers={"User-Agent":"LLM_CHA/0.13.58.82.12 (personal educational assistant)"})
    try:
        with opener(req,timeout=12) as resp:
            payload=json.load(resp)
    except Exception as exc:
        return {"status":"ERROR","hits":[],"error":str(exc)}
    pages=payload.get("query",{}).get("pages",{})
    if not pages:
        return {"status":"NO_HIT","hits":[]}
    words=[x for x in re.split(r"[\s　]+",query) if x]
    candidates=sorted(pages.values(),key=lambda p:p.get("index",999))
    hits=[]
    for page in candidates:
        title=str(page.get("title","")).strip()
        extract=str(page.get("extract","")).strip()
        if not title or not extract or page.get("missing") is not None:
            continue
        # Relevance filter blocks unrelated search hits for a named entity.
        if not all(w.casefold() in (title+" "+extract).casefold() for w in words):
            continue
        hits.append({"title":title,"extract":extract,"url":
                     "https://ja.wikipedia.org/wiki/"+__import__("urllib.parse",fromlist=["quote"]).quote(title.replace(" ","_"))})
        if len(hits)>=MAX_RESULTS:
            break
    return {"status":"HIT" if hits else "NO_HIT","hits":hits}

def format_result(result):
    if result["status"]=="HIT":
        parts=["AI: 【Wikipedia検索結果／外部未検証】"]
        for hit in result["hits"]:
            parts.append(hit["title"]+"\n"+hit["extract"]+"\n出典: "+hit["url"])
        return "\n\n".join(parts)+"\n"
    if result["status"]=="NO_HIT":
        return "AI: 未学習です（Wikipediaにも該当する検索結果がありません）。\n"
    return "AI: Wikipedia検索に接続できませんでした。未学習かどうかは確認できません。\n"
