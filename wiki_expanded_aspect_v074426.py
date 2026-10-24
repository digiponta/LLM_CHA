"""v0.7.44.26: retrieve expanded Wikipedia evidence for selected aspect."""
from wikipedia_acquisition_v0517 import _request
from aspect_evidence_v074425 import extract_aspect
from aspect_relevance_v074427 import ranked_evidence

def expanded_aspect(wiki, aspect, fetch=None):
    if not isinstance(wiki,dict) or wiki.get("status") != "FOUND":
        return None
    title=wiki.get("title","")
    source=wiki.get("url","")
    if not title or not isinstance(source,str) or not source.startswith("https://ja.wikipedia.org/wiki/"):
        return None
    # First consider already available text; then the same article's full extract.
    initial = ranked_evidence(wiki,aspect) or extract_aspect(wiki,aspect)
    try:
        response=_request({"action":"query","prop":"extracts","titles":title,
                           "redirects":1,"explaintext":1,"format":"json",
                           "formatversion":2},fetch)
        pages=response.get("query",{}).get("pages",[])
        if not pages or pages[0].get("missing") or pages[0].get("title") != title:
            return initial
        extended=pages[0].get("extract","")
        if not isinstance(extended,str) or not extended:
            return initial
        return (ranked_evidence({**wiki,"extract":extended},aspect)
                or initial
                or extract_aspect({**wiki,"extract":extended},aspect))
    except (OSError,ValueError,TypeError,KeyError,TimeoutError):
        return initial
