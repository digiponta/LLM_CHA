"""v0.6.28: direct Wikipedia title fetch and multi-article presentation.

Search ambiguity is not a proof of missing exact-title page.
Only show pages actually returned by MediaWiki, and deduplicate redirects.
"""
from urllib.parse import quote
from wikipedia_acquisition_v0517 import _request

def exact_title(term, request_fn=_request):
    try:
        data=request_fn({"action":"query","prop":"extracts|info","titles":term,
                         "redirects":1,"explaintext":1,"exintro":1,
                         "exchars":900,"inprop":"url",
                         "format":"json","formatversion":2})
        pages=data.get("query",{}).get("pages",[])
        if not pages:return None
        page=pages[0]
        summary=page.get("extract","").strip()
        if page.get("missing") or not summary:return None
        title=page.get("title",term)
        return {"title":title,"summary":summary,
                "source":page.get("fullurl") or
                "https://ja.wikipedia.org/wiki/"+quote(title.replace(" ","_")),
                "truth_state":"EXTERNAL_UNVERIFIED"}
    except (OSError,ValueError,KeyError,TimeoutError,TypeError):
        return None

def distinct_pages(pages):
    out=[]
    seen=set()
    for page in pages:
        if page is None:continue
        key=page["title"].replace("_"," ").strip()
        if key in seen:continue
        seen.add(key)
        out.append(page)
    return out

def render_pages(pages):
    return "\n".join("【Wikipedia・{}／未検証】{}\n出典: {}".format(
        p["title"],p["summary"].split("。")[0].strip()+"。",
        p["source"]) for p in distinct_pages(pages))

# v0.8.0.9: do not present another article as the answer to an explicit
# Japanese topic request. Redirects that change the subject require review.
def filter_explicit_topic_pages(pages, question):
    from wiki_topic_switch_guard_v0807 import explicit_topic
    requested=explicit_topic(question)
    if not requested:
        return distinct_pages(pages)
    return [page for page in distinct_pages(pages)
            if page.get("title","").replace("_"," ").strip()==requested]
