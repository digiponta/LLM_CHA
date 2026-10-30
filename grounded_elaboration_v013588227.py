"""Evidence-first elaboration of recovered topics.

Never present raw LLM hypotheses as verified reference facts.
Wikipedia excerpts are explicitly attributed, not silently learned.
"""
import re
from auto_wiki_unknown_v013588212 import search_wikipedia

def summarize_hit(topic,result,max_sentences=4):
 if result.get("status")!="HIT":
  return ("「"+topic+"」について参照可能なWikipediaの説明が見つかりませんでした。"
          "前回のLLM回答だけでは詳細を正確に展開できません。")
 hits=result.get("hits",[])
 # Require named topic matching to avoid irrelevant search-result blending.
 topic_normalized=re.sub(r"\s+","",topic).casefold()
 hit=next((h for h in hits if topic_normalized in
           re.sub(r"\s+","",str(h.get("title",""))).casefold()),None)
 if not hit:
  return "「"+topic+"」と対応する見出しの出典が確認できませんでした。"
 extract=re.sub(r"\s+"," ",str(hit.get("extract",""))).strip()
 sentences=[p.strip() for p in re.split(r"(?<=。)",extract) if p.strip()]
 excerpt="".join(sentences[:max_sentences])[:850]
 if not excerpt:return "出典の記事に詳細説明として利用できる文章がありません。"
 return ("「"+topic+"」について、Wikipediaの説明を紹介するね（外部資料・未検証）。\n"+
         excerpt+"\n出典: "+str(hit.get("url",""))+
         "\n※ 前回のLLM回答に含まれる独自仮説は、この出典で裏付けられたものとは扱いません。")

def elaborate_from_wikipedia(topic,searcher=search_wikipedia):
 result=searcher(topic)
 return {"topic":topic,"status":result.get("status"),"answer":summarize_hit(topic,result)}
