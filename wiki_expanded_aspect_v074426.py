"""v0.7.44.26: retrieve expanded Wikipedia evidence for selected aspect."""
from wikipedia_acquisition_v0517 import _request
from aspect_evidence_v074425 import extract_aspect

def expanded_aspect(wiki, aspect, fetch=None):
    if not isinstance(wiki,dict) or wiki.get("status") != "FOUND":
        return None
    title=wiki.get("title","")
    source=wiki.get("url","")
    if not title or not isinstance(source,str) or not source.startswith("https://ja.wikipedia.org/wiki/"):
        return None
    # First consider already available text; then the same article's full extract.
    answer=extract_aspect(wiki,aspect)
    if answer:
        return answer
    try:
        response=_request({"action":"query","prop":"extracts","titles":title,
                           "redirects":1,"explaintext":1,"format":"json",
                           "formatversion":2},fetch)
        pages=response.get("query",{}).get("pages",[])
        if not pages or pages[0].get("missing") or pages[0].get("title") != title:
            return None
        extended=pages[0].get("extract","")
        if not isinstance(extended,str) or not extended:
            return None
        return extract_aspect({**wiki,"extract":extended},aspect)
    except (OSError,ValueError,TypeError,KeyError,TimeoutError):
        return None
