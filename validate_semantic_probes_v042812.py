"""v0.4.28.12: independent axes for probe agreement and answer relevance.

Only exact normalized text identity is automatically measured. Semantic
equivalence, correctness and relevance require human labels or later evidence.
"""
import argparse,hashlib,json,re
from pathlib import Path

def norm(s):
    return re.sub(r"\s+","",s).strip() if isinstance(s,str) else ""

def analyze(data):
    records=data.get("records")
    if not isinstance(records,list) or len(records)!=64:raise ValueError("expected 64 v042811 records")
    rows=[];seen=set()
    for r in records:
        key=(r.get("id"),r.get("turn"))
        if key in seen:raise ValueError("duplicate turn")
        seen.add(key)
        question=r.get("question");final=r.get("final_answer")
        if not isinstance(question,str) or (final is not None and not isinstance(final,str)):
            raise ValueError("invalid question/answer")
        alignment=r.get("candidate_alignment")
        if alignment not in ("SINGLE_TURN_CONFIRMED","MULTITURN_UNRESOLVED"):
            raise ValueError("invalid alignment")
        events=r.get("observed_candidates")
        if not isinstance(events,list):raise ValueError("invalid candidate list")
        if alignment=="MULTITURN_UNRESOLVED" and events:raise ValueError("unsafe multiturn association")
        texts=[x["text"] for x in events if isinstance(x,dict) and isinstance(x.get("text"),str)]
        if len(texts)!=len(events):raise ValueError("invalid candidate")
        eligible=alignment=="SINGLE_TURN_CONFIRMED" and bool(texts)
        identical=len(set(map(norm,texts)))==1 if eligible else None
        # Literal identity is not semantic agreement, and does not establish relevance.
        rows.append({"id":key[0],"turn":key[1],"question":question,"final_answer":final,
          "gate_resolution":r.get("gate_resolution"),"candidate_alignment":alignment,
          "candidate_count":len(texts) if alignment=="SINGLE_TURN_CONFIRMED" else None,
          "literal_probe_identity":identical,
          "literal_probe_identity_measure":"whitespace_normalized_exact_match",
          "semantic_probe_agreement":"NOT_EVALUATED",
          "question_answer_relevance":"NOT_EVALUATED",
          "gate_decision_quality":"NOT_EVALUATED",
          "manual_review":{"primary_relevant":None,"probes_semantically_equivalent":None,
                           "final_relevant":None,"gate_appropriate":None,"notes":""},
          "review_priority":"HIGH" if r.get("gate_resolution")=="ACCEPT" and eligible else "NORMAL",
          "source_candidate_texts":texts if eligible else [],
          "causal_attribution":"UNDETERMINED"})
    return {"version":"v0.4.28.12","mode":"READ_ONLY_MULTIPLE_AXES",
      "development_only":True,"semantic_scores_estimated":False,
      "total_turns":len(rows),"literal_identity_evaluable":sum(x["literal_probe_identity"] is not None for x in rows),
      "literal_identity_true":sum(x["literal_probe_identity"] is True for x in rows),
      "literal_identity_false":sum(x["literal_probe_identity"] is False for x in rows),
      "manual_relevance_labeled":0,"records":rows}
def main():
    p=argparse.ArgumentParser();p.add_argument("--analysis",required=True);p.add_argument("--output",required=True)
    a=p.parse_args()
    try:
        src,dst=Path(a.analysis),Path(a.output)
        if not src.is_file() or src.is_symlink():raise ValueError("invalid input")
        if dst.exists() or dst.is_symlink():raise ValueError("output exists")
        result=analyze(json.loads(src.read_text(encoding="utf-8")))
        result["input_sha256"]=hashlib.sha256(src.read_bytes()).hexdigest()
        dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({k:result[k] for k in ("total_turns","literal_identity_evaluable","literal_identity_true","literal_identity_false","manual_relevance_labeled")}))
    except (OSError,ValueError,json.JSONDecodeError) as e:p.exit(1,f"probe analysis failed: {e}\n")
if __name__=="__main__":main()
