"""v0.5.46: read-only offline replay of recorded model output and gates.

Input: JSON file containing cases with user, answer, accepted, agreement,
optional topic, evidence_status, needs_repair. No generation or network calls.
Labels are user-supplied; do not infer correctness from Wikipedia absence.
"""
import argparse
import json
from pathlib import Path
from answer_quality_gate_v0542 import evaluate
from dual_quality_gate_v0545 import decide

def replay(cases):
    rows=[]
    for x in cases:
        topic=x.get("topic")
        baseline=evaluate(x["user"],x["answer"],accepted=x["accepted"],
                          agreement=x.get("agreement"),wiki_topic=topic)
        dual=decide(x["user"],x["answer"],accepted=x["accepted"],
                    agreement=x.get("agreement"),topic=topic,
                    evidence_status=x.get("evidence_status"))
        rows.append({"id":x["id"],"label":x.get("needs_repair"),
                     "checkpoint":x.get("checkpoint","UNSPECIFIED"),
                     "baseline_suggest":baseline["suggest_wiki"],
                     "dual_suggest":dual["suggest_wiki"],
                     "evidence_gate":dual["evidence_gate"],
                     "decision":dual["decision"]})
    def scores(field):
        labeled=[r for r in rows if isinstance(r["label"],bool)]
        tp=sum(r["label"] and r[field] for r in labeled)
        fp=sum(not r["label"] and r[field] for r in labeled)
        tn=sum(not r["label"] and not r[field] for r in labeled)
        fn=sum(r["label"] and not r[field] for r in labeled)
        safe=lambda a,b:round(a/b,4) if b else None
        return {"labeled":len(labeled),"tp":tp,"fp":fp,"tn":tn,"fn":fn,
                "precision":safe(tp,tp+fp),"recall":safe(tp,tp+fn)}
    return {"version":"v0.5.46","mode":"OFFLINE_REPLAY","total":len(rows),
            "baseline":scores("baseline_suggest"),"dual_gate":scores("dual_suggest"),
            "cases":rows,"external_verification":False,"auto_lookup":False,"train_ready":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="data/wiki_replay_v0546.json")
    p.add_argument("--output",default=None)
    a=p.parse_args()
    data=json.loads(Path(a.input).read_text(encoding="utf-8"))
    result=replay(data["cases"])
    rendered=json.dumps(result,ensure_ascii=False,indent=2)
    print(rendered)
    if a.output:Path(a.output).write_text(rendered+"\n",encoding="utf-8")

if __name__=="__main__":main()
