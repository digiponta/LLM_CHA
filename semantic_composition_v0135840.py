"""v0.13.58.40: explicit, provenance-bound Semantic Memory composition PoC.

No model training. Exact alias/rule baseline, intentionally NOT an LLM
semantic parser. Unsupported questions abstain. Evaluation items are
development probes, not an independent holdout.
"""
import json,re,argparse,hashlib
from pathlib import Path
SUBJECT="吾輩は猫である"
FACTS={
 "author":{"value":"夏目漱石","source_id":"lit-author"},
 "narrator":{"value":"名前のない猫","source_id":"lit-narrator"},
 "theme":{"value":"猫の視点から人間社会をユーモラスに描く小説","source_id":"theme-stage-3"},
 "title":{"value":"『吾輩は猫である』","source_id":"lit-title"},
}
DEFAULT_PROBES=[
 ("author_alias","『吾輩は猫である』を書いた作家の名前は？",["author"]),
 ("narrator_alias","この小説『吾輩は猫である』は誰の視点で語られる？",["narrator"]),
 ("theme_alias","『吾輩は猫である』で描かれている社会は？",["theme"]),
 ("author_yesno","『吾輩は猫である』を書いたのは漱石ですか？",["author"]),
 ("author_narrator","『吾輩は猫である』の著者と語り手を教えて。",["author","narrator"]),
 ("narrator_theme","夏目漱石の『吾輩は猫である』の視点とテーマを説明して。",["narrator","theme"]),
 ("out_of_scope","量子力学の不確定性原理を教えて",[]),
 ("no_subject","作者は誰？",[])
]
def normalize(s):return re.sub(r"[\s『』「」?？!！。、・]","",s)
def decompose(query):
 q=normalize(query)
 if normalize(SUBJECT) not in q and not ("漱石" in q and "猫の小説" in q):
  return {"relations":[],"reason":"SUBJECT_NOT_GROUNDED"}
 rel=[]
 if any(t in q for t in ("作者","著者","作家","書いた","執筆")):rel.append("author")
 if any(t in q for t in ("語り手","視点","誰の目")):rel.append("narrator")
 if any(t in q for t in ("テーマ","どんな作品","描かれている社会","人間社会")):rel.append("theme")
 if "猫の小説" in q and "漱石" in q and not rel:rel.append("title")
 if not rel:return {"relations":[],"reason":"RELATION_NOT_FOUND"}
 return {"relations":rel,"reason":"RULE_MATCH"}
def answer(query):
 d=decompose(query)
 if not d["relations"]:return {"status":"ABSTAIN",**d,"answer":None,"sources":[]}
 rel=d["relations"]
 chunks={"author":"著者は夏目漱石です","narrator":"語り手は名前のない猫です",
         "theme":"猫の視点から人間社会をユーモラスに描く小説です",
         "title":"作品名は『吾輩は猫である』です"}
 if len(rel)==1 and rel[0]=="author" and "ですか" in query:
  response="はい、著者は夏目漱石です。"
 else:response="。".join(chunks[r] for r in rel)+"。"
 return {"status":"ANSWERED",**d,"answer":response,"sources":[FACTS[r]["source_id"] for r in rel]}
def assess(expected,result):
 return (result["status"]=="ABSTAIN") if not expected else (
  result["status"]=="ANSWERED" and result["relations"]==expected)
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--out",type=Path,default=Path("results/semantic_composition_v0135840.json"))
 a=p.parse_args()
 if a.out.exists():raise FileExistsError(a.out)
 rows=[]
 for ident,question,expected in DEFAULT_PROBES:
  r=answer(question);rows.append({"id":ident,"question":question,"expected_relations":expected,
    "result":r,"rule_route_matches_expected":assess(expected,r)})
 data={"version":"v0.13.58.40","status":"RULE_BASELINE_COMPLETE",
   "parser":"HAND_AUTHORED_RULES","memory_type":"STATIC_APPROVED_FACT_VIEW",
   "trained_model_used":False,"training_performed":False,"independent_holdout":False,
   "facts":FACTS,"evaluations":rows,
   "routing_matches":sum(x["rule_route_matches_expected"] for x in rows),"total":len(rows)}
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":data["status"],"routing_matches":data["routing_matches"],"total":data["total"]},ensure_ascii=False))
 print("report:",a.out)
if __name__=="__main__":main()
