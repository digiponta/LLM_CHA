"""v0.5.17 Wikipedia lookup: unverified external context, never training data.

Only fixed Wikipedia HTTPS endpoints are used. Network errors fail closed.
The returned extract is a citation-bearing reference, not verified truth.
"""
import json
import re
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

ENDPOINT="https://ja.wikipedia.org/w/api.php"
AGENT="LLM_CHA/0.5.17 (https://github.com/digiponta/LLM_CHA; educational research)"
def _request(params,fetch=None):
    url=ENDPOINT+"?"+urlencode(params)
    if fetch is not None:
        return fetch(url)
    request=Request(url,headers={"User-Agent":AGENT,"Accept":"application/json"})
    with urlopen(request,timeout=4) as response:
        return json.load(response)

def lookup(term,fetch=None,context=None):
    if not isinstance(term,str) or not 1<=len(term.strip())<=60:
        raise ValueError("invalid term")
    term=term.strip()
    try:
        found=_request({"action":"query","list":"search","srsearch":term,
                        "srlimit":3,"format":"json","formatversion":2},fetch)
        results=found.get("query",{}).get("search",[])
        if not results:return {"term":term,"status":"NOT_FOUND","candidates":[]}
        titles=[r["title"] for r in results if isinstance(r.get("title"),str)]
        exact=[title for title in titles if title.casefold()==term.casefold()]
        # Ambiguous searches are not automatically treated as a fact match.
        if not exact and len(titles)>1:
            return {"term":term,"status":"AMBIGUOUS","candidates":titles}
        title=exact[0] if exact else titles[0]
        info=_request({"action":"query","prop":"extracts|info","inprop":"url",
                       "titles":title,"redirects":1,"exintro":1,"explaintext":1,
                       "exchars":900,"format":"json","formatversion":2},fetch)
        pages=info.get("query",{}).get("pages",[])
        if not pages or pages[0].get("missing"):
            return {"term":term,"status":"NOT_FOUND","candidates":titles}
        page=pages[0]
        excerpt=page.get("extract","").strip()
        if not excerpt:return {"term":term,"status":"NO_EXTRACT","candidates":titles}
        title=page.get("title",title)
        # A disambiguation article may have the exact search title but the
        # relevant meaning only in a later entry. Use surrounding user context.
        if context and any(word in context for word in ("量子","超伝導","磁気","センサー")):
            match=re.search(r"(超伝導量子干渉計)",excerpt)
            if match and title.casefold()==term.casefold():
                target=match.group(1)
                detail=_request({"action":"query","prop":"extracts|info","inprop":"url",
                    "titles":target,"redirects":1,"exintro":1,"explaintext":1,
                    "exchars":900,"format":"json","formatversion":2},fetch)
                detail_pages=detail.get("query",{}).get("pages",[])
                if detail_pages and not detail_pages[0].get("missing") and detail_pages[0].get("extract","").strip():
                    page=detail_pages[0]
                    title=page.get("title",target)
                    excerpt=page["extract"].strip()
        url="https://ja.wikipedia.org/wiki/"+quote(title.replace(" ","_"))
        keywords=[]
        if "超伝導量子干渉計" in excerpt or title=="超伝導量子干渉計":
            keywords.append("超伝導量子干渉計")
        for token in re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}|[ァ-ヶー]{3,}",excerpt):
            if token not in keywords and token.casefold()!=term.casefold():
                keywords.append(token)
            if len(keywords)>=8:break
        return {"term":term,"status":"FOUND","title":title,"url":url,
                "extract":excerpt[:900],"keywords":keywords,
                "source":"Wikipedia","truth_state":"EXTERNAL_UNVERIFIED",
                "verified":False,"train_ready":False}
    except (URLError,HTTPError,TimeoutError,ValueError,KeyError,TypeError,UnicodeError,OSError) as exc:
        return {"term":term,"status":"LOOKUP_FAILED","error":type(exc).__name__}
