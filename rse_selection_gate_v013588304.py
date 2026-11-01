"""Conservative RSE selection gate: candidate audit, never automatic CP impersonation.

Separates user question from source question; flags incompatible temporal/intent
slots and autobiographical human answers. Non-blocked candidates still require review.
"""
import argparse,json,re
from pathlib import Path
from rse_intent_router_v013588302 import route

def slots(question):
    q=question.strip()
    return {
      "current_activity":bool(re.search(r"今何して|今日は何して|今.*何.*して",q)),
      "enjoyment":bool(re.search(r"楽しい|好き|趣味|楽しみ",q)),
      "quantified_state":bool(re.search(r"何点|何パーセント|何%|どれぐらい|どのくらい|マックス|満点",q)),
      "current_state":bool(re.search(r"最近どう|元気|調子はどう",q)),
    }

def gate(query,source_question,source_answer):
    intended=route(query);original=route(source_question)
    need=slots(query);origin=slots(source_question)
    reasons=[]
    if intended["intent"]!=original["intent"] or intended["route"]!=original["route"]:
        reasons.append("INTENT_MISMATCH")
    for key in ("current_activity","enjoyment","quantified_state"):
        if need[key]!=origin[key]:
            reasons.append("SLOT_MISMATCH_"+key.upper())
    # Never adopt first-person claims or subjective physical states of a human speaker.
    if re.search(r"(私|僕|俺|うち|家族|実家|仕事|学校|住ん|飼っ|行った|買った|食べた|書いてる|元気です|９０|90|夕方)",source_answer):
        reasons.append("POTENTIAL_PERSONA_TRANSFER")
    return {"status":"REJECT" if reasons else "MANUAL_REVIEW_REQUIRED",
            "reasons":reasons,
            "question_intent":intended["intent"],"source_intent":original["intent"],
            "query_slots":need,"source_slots":origin,
            "response_automatically_approved":False,
            "semantic_relevance_verified":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data",default="data/real_persona_pilot_v013588293.jsonl")
    p.add_argument("--question",required=True)
    p.add_argument("--ids",type=int,nargs="+",required=True)
    p.add_argument("--report",default="results/rse_selection_gate_v013588304.json")
    a=p.parse_args()
    wanted=set(a.ids);out=[]
    for i,line in enumerate(Path(a.data).read_text(encoding="utf-8-sig").splitlines()):
        if i not in wanted:continue
        row=json.loads(line)
        out.append({"id":i,**gate(a.question,row["user"],row["assistant"])})
    result={"status":"AUDIT_ONLY","requested_ids":a.ids,"rows":out,"candidate_text_exported":False}
    dest=Path(a.report);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
