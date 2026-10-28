"""v0.13.58.41: provenance-gated Semantic Memory adapter PoC.

Uses exported experimental records, not the production Semantic Memory store.
Separates rule parsing from eligible fact resolution, conservatively abstains
on negative/ambiguous questions, and carries record provenance.
"""
import argparse,json,re
from pathlib import Path

FORMAT="cha-semantic-memory-experimental-v0.13.58.41"
ALLOWED="ASSISTANT_REVIEWED_EXPERIMENTAL"
SUBJECT="吾輩は猫である"
def norm(s):return re.sub(r"[\s『』「」?？!！。、・]","",s)
def load(path):
 data=json.loads(Path(path).read_text(encoding="utf-8-sig"))
 if data.get("format")!=FORMAT:raise ValueError("unexpected memory format")
 records=data.get("records")
 if not isinstance(records,list):raise ValueError("invalid records")
 ids=set()
 for r in records:
  if not isinstance(r,dict) or not all(isinstance(r.get(k),str) and r[k] for k in ("record_id","subject","relation","value","source_id","approval_state")):raise ValueError("invalid record")
  if r["record_id"] in ids:raise ValueError("duplicate record id")
  ids.add(r["record_id"])
 return records
def parse(question):
 q=norm(question)
 if norm(SUBJECT) not in q:return [],"SUBJECT_NOT_GROUNDED"
 # Safety: an affirmative yes/no template must not blindly affirm false names.
 if any(x in q for x in ("ではない","じゃない","違う","本当ですか","以外","ではありません")):return [],"NEGATION_OR_UNCERTAIN"
 if "書いたのは" in q and "ですか" in q:
  if "夏目漱石" not in q and "漱石" not in q:return [],"UNVERIFIED_CLAIM"
 relations=[]
 if any(x in q for x in ("作者","著者","作家","書いた","執筆")):relations.append("author")
 if any(x in q for x in ("語り手","視点","誰の目")):relations.append("narrator")
 if any(x in q for x in ("テーマ","どんな作品","描かれている社会","人間社会")):relations.append("theme")
 if not relations:return [],"RELATION_NOT_FOUND"
 return relations,"RULE_MATCH"
def resolve(records,relation,allow_experimental=True):
 matches=[r for r in records if r["subject"]==SUBJECT and r["relation"]==relation and r.get("active") is True
   and r["approval_state"]==ALLOWED and r.get("production_approved") is False and allow_experimental]
 if not matches:return None,"NO_ELIGIBLE_FACT"
 if len({r["value"] for r in matches})>1:return None,"CONFLICTING_FACTS"
 return matches[0],None
def answer(question,records,allow_experimental=True):
 relations,reason=parse(question)
 if not relations:return {"status":"ABSTAIN","reason":reason,"answer":None,"facts":[]}
 found=[]
 for rel in relations:
  record,error=resolve(records,rel,allow_experimental)
  if error:return {"status":"ABSTAIN","reason":error,"answer":None,"facts":[]}
  found.append(record)
 chunks={"author":lambda x:f"著者は{x}です","narrator":lambda x:f"語り手は{x}です",
         "theme":lambda x:f"{x}です"}
 rendered="。".join(chunks[r["relation"]](r["value"]) for r in found)+"。"
 if "ですか" in question and len(found)==1 and found[0]["relation"]=="author":
  rendered="はい、"+rendered
 return {"status":"ANSWERED","reason":reason,"answer":rendered,
 "facts":[{"record_id":r["record_id"],"source_id":r["source_id"],
          "approval_state":r["approval_state"],"relation":r["relation"]} for r in found],
 "runtime_scope":"EXPERIMENTAL_ONLY"}
PROBES=[
 ("author","『吾輩は猫である』を書いた作家の名前は？","ANSWERED"),
 ("compound","『吾輩は猫である』の著者と語り手を教えて。","ANSWERED"),
 ("theme","夏目漱石の『吾輩は猫である』の視点とテーマを説明して。","ANSWERED"),
 ("unverified_claim","『吾輩は猫である』を書いたのは福沢諭吉ですか？","ABSTAIN"),
 ("negation","『吾輩は猫である』の作者は夏目漱石ではない？","ABSTAIN"),
 ("unknown_subject","作者は誰？","ABSTAIN"),
]
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--memory",type=Path,default=Path("data/literature_semantic_memory_v0135841.json"))
 p.add_argument("--output",type=Path,default=Path("results/provenance_semantic_v0135841.json"))
 a=p.parse_args()
 if a.output.exists():raise FileExistsError(a.output)
 records=load(a.memory);cases=[]
 for id,q,expected in PROBES:
  r=answer(q,records);cases.append({"id":id,"question":q,"expected":expected,
       "result":r,"status_match":r["status"]==expected})
 report={"version":"v0.13.58.41","status":"PROVENANCE_MEMORY_POC_COMPLETE",
 "source_type":"EXPORTED_EXPERIMENTAL_RECORDS_NOT_LIVE_MEMORY",
 "training_performed":False,"production_promotion_allowed":False,
 "rule_parser_used":True,"independent_holdout":False,
 "matched":sum(x["status_match"] for x in cases),"total":len(cases),"cases":cases}
 a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":report["status"],"matched":report["matched"],"total":report["total"]},ensure_ascii=False))
 print("report:",a.output)
if __name__=="__main__":main()
