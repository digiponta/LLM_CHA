"""Read-only adapter: verified Semantic Memory first, theme-based RSE second.

The caller must provide memory results with explicit verified/approved status.
Never infer truth from a text match, and never mutate chat.py or model weights.
"""
import argparse,json
from pathlib import Path
from rse_semantic_theme_v013588312 import select,UNLEARNED

def decide(query,memory_records,candidates):
    audit=[]
    for i,record in enumerate(memory_records):
        match=record.get("query")==query
        approved=record.get("approved") is True
        verified=record.get("verified") is True
        answer=record.get("answer")
        audit.append({"id":str(record.get("id",i)),"exact_query":match,
                      "approved":approved,"verified":verified})
        if match and approved and verified and isinstance(answer,str) and answer.strip():
            return {"status":"MEMORY_SELECTED","answer":answer,"source":"SEMANTIC_MEMORY_VERIFIED",
                    "candidate_id":str(record.get("id",i)),"memory_audit":audit,
                    "theme_trace":[],"live_integration":False}
    result=select(query,candidates)
    return {"status":result["status"],"answer":result["answer"],
            "source":"THEME_RSE" if result["status"]=="ANSWER_SELECTED" else "NO_APPROVED_MATCH",
            "candidate_id":result["candidate_id"],"memory_audit":audit,
            "theme_trace":result["trace"],"live_integration":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--query",required=True)
    p.add_argument("--data",default="data/rse_memory_theme_examples_v013588313.json")
    args=p.parse_args()
    obj=json.loads(Path(args.data).read_text(encoding="utf-8-sig"))
    print(json.dumps(decide(args.query,obj.get("memory_records",[]),obj.get("candidates",[])),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
