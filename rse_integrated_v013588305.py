"""Audit-only integrated RSE: intent -> candidate shortlist -> gate -> safe fallback.

No source-speaker answer is emitted as an assistant reply. Factual requests defer
to existing Semantic Memory; other requests defer to content RSE.
"""
import argparse,json
from pathlib import Path
from rse_intent_router_v013588302 import evaluate
from rse_intent_candidates_v013588303 import create_index,rank
from rse_selection_gate_v013588304 import gate

def integrate(question,records,top_k=5):
    routed=evaluate(question)
    if routed["route"]!="DIALOGUE_INTENT":
        return {"status":routed["status"],"intent":routed["intent"],"proposed_response":None,
                "source":"DEFER","candidates":[],"automatic_source_reply":False}
    indexed=create_index(records)
    selected=rank(indexed,question,top_k)
    by_id={x["id"]:x for x in indexed}
    checked=[]
    for candidate in selected["candidates"]:
        source=by_id[candidate["id"]]
        check=gate(question,source["question"],source["answer"])
        checked.append({"id":source["id"],"gate_status":check["status"],"reasons":check["reasons"]})
    return {"status":"SAFE_FALLBACK_PROPOSED",
            "intent":routed["intent"],"source":"ASSISTANT_SAFE_TEMPLATE",
            "proposed_response":routed["response"],
            "candidate_pool":selected.get("candidate_pool",0),
            "candidates":checked,
            "rejected":sum(c["gate_status"]=="REJECT" for c in checked),
            "manual_review":sum(c["gate_status"]=="MANUAL_REVIEW_REQUIRED" for c in checked),
            "automatic_source_reply":False,"expansion_enabled":False,
            "candidate_text_exported":False,"human_quality_verified":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data",default="data/real_persona_pilot_v013588293.jsonl")
    p.add_argument("--question",required=True)
    p.add_argument("--top-k",type=int,default=5)
    p.add_argument("--report",default="results/rse_integrated_v013588305.json")
    a=p.parse_args()
    if not 1<=a.top_k<=30:raise ValueError("top-k must be 1..30")
    records=[json.loads(line) for line in Path(a.data).read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    result=integrate(a.question,records,a.top_k)
    output=Path(a.report);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
