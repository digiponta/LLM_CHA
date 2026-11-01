"""RSE phase 1.3: rank human conversation answer candidates by source-question intent.

Read-only: never automatically present CP's responses as an AI identity.
"""
import argparse,json,re
from collections import Counter
from pathlib import Path
from rse_intent_router_v013588302 import route,evaluate

def safe_token_count(text):
    return len(re.findall(r"[一-龥ぁ-ゖァ-ヺA-Za-z0-9]+",text))
def possible_personal_claim(answer):
    # High-recall warning heuristic, not privacy verification.
    return bool(re.search(r"(私|僕|俺|うち|家族|実家|仕事|学校|住ん|飼っ|行った|買った|食べた|昨日)",answer))
def create_index(records):
    entries=[]
    for i,r in enumerate(records):
        q=r.get("user");ans=r.get("assistant")
        if not isinstance(q,str) or not isinstance(ans,str) or not q.strip() or not ans.strip():continue
        x=route(q)
        entries.append({"id":i,"intent":x["intent"],"route":x["route"],"question":q,
                        "answer":ans,"personal_claim_warning":possible_personal_claim(ans),
                        "answer_length":len(ans)})
    return entries
def rank(entries,question,top_k=5):
    intent=route(question)
    if intent["route"]!="DIALOGUE_INTENT":
        return {"status":"DEFER","target_route":intent["route"],"intent":intent["intent"],
                "candidates":[],"automatic_reply":False}
    matched=[e for e in entries if e["intent"]==intent["intent"] and e["route"]=="DIALOGUE_INTENT"]
    # Deterministic baseline: non-personal and moderate-length answer preferred.
    matched.sort(key=lambda e:(e["personal_claim_warning"],abs(e["answer_length"]-24),e["id"]))
    return {"status":"REVIEW_CANDIDATES" if matched else "NO_MATCH",
            "intent":intent["intent"],"candidate_pool":len(matched),
            "fallback_template":evaluate(question)["response"],
            "candidates":[{"id":e["id"],"answer_length":e["answer_length"],
                           "personal_claim_warning":e["personal_claim_warning"]} for e in matched[:top_k]],
            "automatic_reply":False,"semantic_relevance_verified":False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data",default="data/real_persona_pilot_v013588293.jsonl")
    p.add_argument("--question",required=True)
    p.add_argument("--top-k",type=int,default=5)
    p.add_argument("--report",default="results/rse_intent_candidates_v013588303.json")
    p.add_argument("--show-answers",action="store_true")
    a=p.parse_args()
    if not 1<=a.top_k<=30:raise ValueError("top-k must be 1..30")
    rows=[json.loads(l) for l in Path(a.data).read_text(encoding="utf-8-sig").splitlines() if l.strip()]
    index=create_index(rows);result=rank(index,a.question,a.top_k)
    target=Path(a.report);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if a.show_answers and result["status"]=="REVIEW_CANDIDATES":
        by_id={x["id"]:x for x in index}
        result={**result,"local_only_answers":[{"id":c["id"],"question":by_id[c["id"]]["question"],
                                                  "answer":by_id[c["id"]]["answer"]} for c in result["candidates"]]}
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
