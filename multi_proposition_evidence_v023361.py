"""v0.2.33.61 — multi-proposition inclusion-chain experiment.

Only the explicitly configured 'includes' relation is treated as transitive.
All premises must be TRUE, source-backed, and share the same condition.
Counterevidence on the requested pair blocks the inference.
This is isolated proof-chain validation, not production Semantic Memory mutation.
"""
from dataclasses import dataclass
from collections import deque
import re
from structural_semantic_consistency_v023359 import parse,clean

@dataclass(frozen=True)
class Evidence:
    statement:str
    truth:str
    source:str
    evidence_id:str

def validate(items,candidate,*,transitive_relations=frozenset()):
    target=parse(candidate)
    if target is None:return {"status":"blocked","reason":"unsupported_candidate","path":[]}
    relation,src,dst,positive,condition=target
    if relation!="includes" or not positive or relation not in transitive_relations:
        return {"status":"blocked","reason":"transitivity_not_authorized","path":[]}
    edges={};counter=[]
    for e in items:
        p=parse(e.statement)
        if p is None:continue
        rel,a,b,polarity,cond=p
        if rel!=relation or cond!=condition:continue
        if (a,b)==(src,dst) and not polarity and e.truth=="TRUE" and e.source:
            counter.append(e.evidence_id)
        if not polarity or e.truth!="TRUE" or not e.source or not e.evidence_id:continue
        edges.setdefault(a,[]).append((b,e.evidence_id))
    if counter:return {"status":"blocked","reason":"explicit_counterevidence",
                       "path":[],"counterevidence":counter}
    queue=deque([(src,[],{src})])
    while queue:
        node,path,seen=queue.popleft()
        for next_node,eid in edges.get(node,()):
            if next_node in seen:continue
            chain=path+[eid]
            if next_node==dst:
                return {"status":"supported","reason":"authorized_inclusion_chain",
                        "path":chain,"condition":condition,"relation":relation}
            queue.append((next_node,chain,seen|{next_node}))
    return {"status":"blocked","reason":"no_complete_evidence_chain","path":[]}

def evaluate():
    def E(s,i,truth="TRUE",source="reviewed-fixture"):
        return Evidence(s,truth,source,i)
    base=[E("AはBを含む","e1"),E("BはCを含む","e2")]
    cases=[
        ("authorized_chain",base,"AはCを含む",{"includes"},"supported","authorized_inclusion_chain"),
        ("not_authorized",base,"AはCを含む",set(),"blocked","transitivity_not_authorized"),
        ("missing_link",[base[0]],"AはCを含む",{"includes"},"blocked","no_complete_evidence_chain"),
        ("unverified_link",[base[0],E("BはCを含む","e2","UNVERIFIED")],"AはCを含む",{"includes"},"blocked","no_complete_evidence_chain"),
        ("negative_link",[base[0],E("BはCを含まない","e2")],"AはCを含む",{"includes"},"blocked","no_complete_evidence_chain"),
        ("reversed_link",[base[0],E("CはBを含む","e2")],"AはCを含む",{"includes"},"blocked","no_complete_evidence_chain"),
        ("condition_mismatch",[E("条件XではAはBを含む","e1"),E("条件YではBはCを含む","e2")],
            "条件XではAはCを含む",{"includes"},"blocked","no_complete_evidence_chain"),
        ("condition_match",[E("条件XではAはBを含む","e1"),E("条件XではBはCを含む","e2")],
            "条件XではAはCを含む",{"includes"},"supported","authorized_inclusion_chain"),
        ("counterevidence",base+[E("AはCを含まない","e3")],"AはCを含む",
            {"includes"},"blocked","explicit_counterevidence"),
        ("untrusted_source",[base[0],E("BはCを含む","e2",source="")],
            "AはCを含む",{"includes"},"blocked","no_complete_evidence_chain"),
        ("unsupported_candidate",base,"AはCである",{"includes"},"blocked","transitivity_not_authorized"),
    ]
    rows=[]
    for name,evidence,candidate,allowed,want_status,want_reason in cases:
        result=validate(evidence,candidate,transitive_relations=frozenset(allowed))
        ok=result["status"]==want_status and result["reason"]==want_reason
        if name in ("authorized_chain","condition_match"):
            ok=ok and result["path"]==["e1","e2"]
        rows.append({"case":name,"passed":ok,"actual":result,
                     "expected_status":want_status,"expected_reason":want_reason})
    return {"version":"v0.2.33.61","total":len(rows),
            "passed":sum(r["passed"] for r in rows),"cases":rows,
            "scope":"deterministic isolated evidence-fixture chain validation",
            "production_semantic_memory_changed":False,"model_training":False}

def main():
    import argparse,json
    from pathlib import Path
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="results/multi_proposition_evidence_v023361.json")
    args=p.parse_args()
    report=evaluate()
    out=Path(args.out)
    if out.exists():raise FileExistsError("Refusing overwrite: "+str(out))
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"LLM_CHA v0.2.33.61: {report['passed']}/{report['total']} PASS")
    for r in report["cases"]:print(("PASS" if r["passed"] else "FAIL"),r["case"],r["actual"]["reason"])
    print("Saved:",out)
    if report["passed"]!=report["total"]:raise SystemExit(1)
if __name__=="__main__":main()
