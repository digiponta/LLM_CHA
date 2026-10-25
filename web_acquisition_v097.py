"""v0.9.7 read-only Web acquisition to unapproved local review queue.

Intentionally no automatic Semantic Memory promotion, /sleep or training.
Only explicit HTTP(S) URLs; private-network requests and redirects are denied.
"""
import argparse
import html
import ipaddress
import json
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path

MAX_BYTES=500_000
UA="LLM-CHA-ResearchBot/0.9.7 (manual research acquisition)"
def validate_url(url):
    u=urllib.parse.urlsplit(url)
    if u.scheme not in ("https","http") or not u.hostname or u.username or u.password:
        raise ValueError("Only absolute HTTP(S) URLs without credentials allowed")
    if u.port not in (None,80,443):
        raise ValueError("Nonstandard port disallowed")
    hostname=u.hostname.rstrip(".").lower()
    if hostname in ("localhost",) or hostname.endswith((".local",".localhost",".internal")):
        raise ValueError("Internal host denied")
    answers=socket.getaddrinfo(hostname,u.port or (443 if u.scheme=="https" else 80),type=socket.SOCK_STREAM)
    for answer in answers:
        ip=ipaddress.ip_address(answer[4][0])
        if not ip.is_global:
            raise ValueError("Non-public address denied")
    return url

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        raise ValueError("Redirects denied; inspect final URL separately")

def extract_text(raw):
    # Conservative plaintext extraction with markup removal, not a full browser.
    text=raw.decode("utf-8","replace")
    text=re.sub(r"(?is)<(script|style|nav|footer|header)\b[^>]*>.*?</\1>"," ",text)
    title=re.search(r"(?is)<title[^>]*>(.*?)</title>",text)
    title=html.unescape(re.sub("<[^>]+>"," ",title.group(1))).strip() if title else ""
    text=re.sub(r"(?is)<[^>]+>"," ",text)
    text=html.unescape(text)
    text=re.sub(r"\s+"," ",text).strip()
    return title,text[:15000]

def acquire(url,queue_file,fetcher=None):
    validate_url(url)
    if fetcher is None:
        opener=urllib.request.build_opener(NoRedirect())
        # robots.txt checked under same origin, using the same conservative rules
        parsed=urllib.parse.urlsplit(url)
        robots_url=f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        try:
            with opener.open(urllib.request.Request(robots_url,headers={"User-Agent":UA}),timeout=10) as response:
                if response.status != 200:
                    raise ValueError("robots.txt returned an unexpected status")
                robots_body=response.read(100000).decode("utf-8","replace")
        except urllib.error.HTTPError as exc:
            # RFC 9309 §2.3.1.3: 4xx robots.txt responses are unavailable,
            # not evidence of disallow. Only handle 404 here deliberately.
            if exc.code == 404:
                robots_body = None
            else:
                raise ValueError(f"robots.txt HTTP {exc.code}; refusing acquisition") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ValueError("robots.txt unavailable due to network error; refusing acquisition") from exc
        if robots_body is not None:
            rules=urllib.robotparser.RobotFileParser()
            rules.parse(robots_body.splitlines())
            if not rules.can_fetch(UA,url):
                raise ValueError("Robots policy disallows this request")
        with opener.open(urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html"}),timeout=15) as response:
            if response.status!=200 or "text/html" not in response.headers.get("Content-Type","").lower():
                raise ValueError("Only successful HTML responses are supported")
            raw=response.read(MAX_BYTES+1)
    else:
        # Test seam; production callers should not supply alternate fetchers.
        raw=fetcher(url)
    if len(raw)>MAX_BYTES:
        raise ValueError("Page too large")
    title,text=extract_text(raw)
    if len(text)<80:
        raise ValueError("Not enough extractable text")
    item={"schema":"web_pending_v097","url":url,"title":title,
          "excerpt":text[:3000],"retrieved_at":datetime.now(timezone.utc).isoformat(),
          "state":"PENDING_REVIEW","truth_state":"EXTERNAL_UNVERIFIED",
          "train_ready":False,"auto_promote":False,
          "candidate_origin":"WEB_HTML_EXTRACTION",
          "review_required":["source_reliability","copyright_permission","fact_validation","prompt_injection"]}
    output=Path(queue_file)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("a",encoding="utf-8") as fh:
        fh.write(json.dumps(item,ensure_ascii=False)+"\n")
    return item

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--queue",default="data/web_pending_v097.jsonl")
    args=parser.parse_args()
    record=acquire(args.url,args.queue)
    print(json.dumps({"status":"PENDING_REVIEW","url":record["url"],"title":record["title"],
                      "train_ready":False},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
