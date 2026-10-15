"""v0.5.61 optional Google Search fallback through SerpApi (third-party).

The Google Search official/deprecated API is NOT used. No direct Google HTML
scraping. Search snippets are UNVERIFIED leads, not factual evidence for
automatic training, promotion or a source-grounded knowledge answer.
"""
import json
import os
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

ENDPOINT="https://serpapi.com/search.json"

def search(term,api_key=None,fetch=None):
    term=str(term).strip() if term is not None else ""
    if not 1<=len(term)<=80:return {"status":"INVALID_QUERY","results":[]}
    key=api_key if api_key is not None else os.environ.get("SERPAPI_API_KEY","")
    if not key:return {"status":"NOT_CONFIGURED","results":[]}
    params={"engine":"google","q":term,"hl":"ja","gl":"jp","num":5,"api_key":key}
    try:
        if fetch is None:
            request=Request(ENDPOINT+"?"+urlencode(params),headers={"Accept":"application/json"})
            with urlopen(request,timeout=8) as response:data=json.load(response)
        else:
            data=fetch(params)
        if not isinstance(data,dict) or data.get("error"):
            return {"status":"SEARCH_FAILED","results":[]}
        results=[]
        for item in data.get("organic_results",[])[:5]:
            if not isinstance(item,dict):continue
            link=item.get("link","")
            parsed=urlparse(link)
            if parsed.scheme!="https" or not parsed.netloc:continue
            title=str(item.get("title","")).strip()[:160]
            snippet=str(item.get("snippet","")).strip()[:350]
            if not title:continue
            results.append({"title":title,"url":link,"snippet":snippet,
                            "truth_state":"EXTERNAL_UNVERIFIED",
                            "train_ready":False})
        return {"status":"FOUND" if results else "NO_RESULTS",
                "query":term,"results":results,
                "provider":"SERPAPI_GOOGLE","verified":False,
                "train_ready":False,"auto_promote":False}
    except (OSError,ValueError,TypeError,KeyError,TimeoutError) as exc:
        return {"status":"SEARCH_FAILED","reason":type(exc).__name__,"results":[]}

def render_leads(report,persona="nagato"):
    if report.get("status")!="FOUND":return None
    items=report["results"]
    heading=("Wikipediaでは十分な資料を得られなかった。Google検索の参考候補を示す。"
             if persona=="nagato" else
             "Wikipediaでは十分な資料を取得できなかったため、Google検索の参考候補を示します。")
    lines=[heading]
    for i,item in enumerate(items[:3],1):
        lines.append(f"{i}. {item['title']} — {item['url']}")
    lines.append("検索結果は未検証。内容を確認していないので、事実として断定・学習しない。")
    return {"answer":"\n".join(lines),"route":"GOOGLE_SEARCH_LEADS",
            "verified":False,"train_ready":False,"auto_promote":False}
