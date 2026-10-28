"""v0.13.58.7 resilient wrapper for the v0.13.58.6 Wikipedia ingester.

Cache successful article responses by requested title, so reruns after an
HTTP 503 resume without refetching pages. Retry only 429/502/503/504 with
bounded exponential backoff and Retry-After. Does not bypass rate limits.
"""
import argparse,datetime,email.utils,hashlib,json,sys,time,urllib.error
from pathlib import Path
import ingest_wikipedia_foundation_v013586 as previous

RETRYABLE={429,502,503,504}
def retry_seconds(value,attempt,cap=120):
    if value:
        try:
            seconds=float(value)
        except (TypeError,ValueError):
            try:
                dt=email.utils.parsedate_to_datetime(value)
                seconds=(dt-datetime.datetime.now(datetime.timezone.utc)).total_seconds()
            except (TypeError,ValueError,OverflowError):
                seconds=None
        if seconds is not None:return max(0.0,min(float(cap),seconds))
    return min(float(cap),float(2**(attempt+1)))

def resilient_fetch(title,original,cache_dir,max_retries=2,sleep=time.sleep):
    if max_retries<0 or max_retries>5:raise ValueError("max_retries outside 0..5")
    key=hashlib.sha256(title.encode("utf-8")).hexdigest()
    target=cache_dir/(key+".json")
    if target.is_file():
        cached=json.loads(target.read_text(encoding="utf-8"))
        if cached.get("requested_title")!=title:raise ValueError("cache title mismatch")
        return cached["page"]
    for attempt in range(max_retries+1):
        try:
            page=original(title)
            cache_dir.mkdir(parents=True,exist_ok=True)
            # Missing articles are cached to prevent redundant requests.
            tmp=cache_dir/(key+".partial")
            with tmp.open("w",encoding="utf-8") as f:
                json.dump({"requested_title":title,"page":page},f,ensure_ascii=False)
            tmp.replace(target)
            return page
        except urllib.error.HTTPError as error:
            if error.code not in RETRYABLE or attempt==max_retries:
                raise
            wait=retry_seconds(error.headers.get("Retry-After") if error.headers else None,attempt)
            print(f"retryable HTTP {error.code} for {title}; backoff {wait:.1f}s ({attempt+1}/{max_retries})",file=sys.stderr)
            sleep(wait)
        except urllib.error.URLError:
            # Network errors are not assumed transient.
            raise

def main():
    ap=argparse.ArgumentParser(description="Resumable Wikipedia source ingestion")
    ap.add_argument("--cache-dir",type=Path,default=Path("results/wikipedia_cache_v013587"))
    ap.add_argument("--max-retries",type=int,default=2)
    args,rest=ap.parse_known_args()
    if not 0<=args.max_retries<=5:ap.error("max-retries must be 0..5")
    original=previous.query_article
    def fetch(title,user_agent,timeout=30):
        return resilient_fetch(title,lambda t:original(t,user_agent,timeout),args.cache_dir,args.max_retries)
    previous.query_article=fetch
    sys.argv=[sys.argv[0],*rest]
    previous.main()

if __name__=="__main__":main()
