"""Open an explicitly requested Google search in the user's browser.

This module does not scrape Google results, fetch pages, or write training data.
"""
import argparse
import re
import urllib.parse
import webbrowser

SEARCH_BASE="https://www.google.co.jp/search"

def search_intent(text):
    text=str(text or "").strip().rstrip("。！？!? ")
    patterns=(r"(.+?)を[グぐ][グぐ]って",r"(.+?)で[グぐ][グぐ]って",r"(.+?)をGoogleで検索して",
              r"(.+?)を検索して")
    for pattern in patterns:
        m=re.fullmatch(pattern,text,re.IGNORECASE)
        if m:
            term=m.group(1).strip()
            return term if term and len(term)<=120 and not term.startswith("/") else None
    return None

def search_url(query):
    if not isinstance(query,str) or not query.strip() or len(query)>120:
        raise ValueError("Nonempty search term of at most 120 characters required")
    return SEARCH_BASE+"?"+urllib.parse.urlencode({"q":query})

def launch(query, opener=None):
    url=search_url(query)
    opened=(opener or webbrowser.open)(url)
    return {"route":"WEB_SEARCH_BROWSER","query":query,"url":url,
            "opened":bool(opened),"results_collected":False,
            "train_ready":False,"auto_promote":False}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--url-only",action="store_true")
    args=parser.parse_args()
    if args.url_only:
        print(search_url(args.query))
    else:
        print(launch(args.query))

if __name__=="__main__":
    main()
