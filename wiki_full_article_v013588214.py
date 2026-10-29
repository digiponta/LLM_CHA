"""Full Wikipedia wikitext attribute retrieval; no inference from neighboring facts."""
import json
import re
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen
from wiki_topic_attribute_v013588213 import resolve_question, search_for_question, ALIASES

LABELS={
 "屈折率":("屈折率","refractive_index","refractive index"),
 "硬度":("モース硬度","硬度","mohs","hardness"),
 "化学組成":("化学組成","化学式","組成","formula"),
 "産地":("産地","産出地","産出"),
}
def fetch_full_article(title,opener=urlopen):
 params=urlencode({"action":"query","prop":"revisions","rvprop":"content",
                   "rvslots":"main","format":"json","titles":title,
                   "redirects":"1"})
 req=Request("https://ja.wikipedia.org/w/api.php?"+params,
             headers={"User-Agent":"LLM_CHA/0.13.58.82.14 (research client)"})
 try:
  with opener(req,timeout=15) as response:
   payload=json.load(response)
  pages=list(payload.get("query",{}).get("pages",{}).values())
  if not pages or "missing" in pages[0]:
   return None
  page=pages[0]
  rev=page.get("revisions",[{}])[0]
  text=rev.get("slots",{}).get("main",{}).get("*",rev.get("*",""))
  return {"title":page.get("title",title),"wikitext":text}
 except Exception:
  return None

def find_attribute_line(wikitext,attribute):
 labels=LABELS[attribute]
 for line in wikitext.splitlines():
  stripped=line.strip()
  # Infobox property must be on the LHS of an assignment.
  match=re.match(r"^\|\s*([^=|]{1,55})\s*=\s*(.{1,220})$",stripped)
  if match and any(label.casefold() in match.group(1).casefold() for label in labels):
   value=match.group(2).strip()
   # Avoid wiki markup, nested templates, references and missing values.
   if value and not any(x in value for x in ("{{","}}","[[","]]","<ref","<!--","|")):
    return stripped
  # Plain text statement: topic-relevant sentence checked elsewhere.
  if len(stripped)>250 or stripped.startswith(("{{","|","[[","!","*")):
   continue
  if any(label in stripped for label in labels):
   match=re.search(r"(?:である|は|が)\s*([0-9]+(?:[.．][0-9]+)?(?:\s*[〜～\-–]\s*[0-9]+(?:[.．][0-9]+)?)?)",stripped)
   if match:
    return stripped
 return None

def resolve_full(question,active_topic="",searcher=search_for_question,fetcher=fetch_full_article):
 first=searcher(question,active_topic)
 if first.get("status")!="NO_ATTRIBUTE_EVIDENCE":
  return first
 topic=first["topic"];attribute=first["attribute"]
 # A search hit established the topic; do not scan unrelated articles.
 general=searcher(topic,"")
 if general.get("status")!="HIT" or not general.get("hits"):
  return first
 title=general["hits"][0]["title"]
 article=fetcher(title)
 if not article:
  return first
 line=find_attribute_line(article["wikitext"],attribute)
 if not line:
  return first
 return {"status":"HIT","topic":topic,"attribute":attribute,
         "hits":[{"title":article["title"],"extract":line,
                  "url":"https://ja.wikipedia.org/wiki/"+quote(article["title"].replace(" ","_"))}],
         "evidence_type":"WIKITEXT_ATTRIBUTE","truth_state":"EXTERNAL_UNVERIFIED"}
