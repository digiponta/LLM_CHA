"""v0.6.35 Semantic-Memory-First experiment (isolated, read-only model).

Reviewed exact QA facts are served from a local JSONL overlay. This is not
model-weight learning and does not modify production Semantic Memory or chat.py.
"""
import argparse
import hashlib
import json
from pathlib import Path
from evaluate_online_quality_v0632 import load_cases, score
from response_quality_gate_v0633 import gate_quality_report

def norm(text):
    return " ".join(str(text).strip().split())

def load_overlay(path):
    facts={}
    for lineno,line in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(),1):
        if not line.strip():continue
        row=json.loads(line)
        if row.get("status")!="approved":
            continue
        question,answer=norm(row.get("question","")),norm(row.get("answer",""))
        if not question or not answer or not row.get("source_id"):
            raise ValueError(f"invalid approved entry line {lineno}")
        if question in facts and facts[question]["answer"]!=answer:
            raise ValueError(f"conflicting approved entries for {question}")
        facts[question]={"answer":answer,"source_id":row["source_id"]}
    return facts

def evaluate(baseline_report, cases, overlay):
    before=baseline_report["answers"]["before"]
    output_before={}
    output_after={}
    provenance={}
    keyword_after={}
    for case in cases:
        key=case["id"]
        if key not in before:
            raise ValueError("missing baseline answer: "+key)
        output_before[key]=before[key]
        hit=overlay.get(norm(case["prompt"]))
        output_after[key]=hit["answer"] if hit else before[key]
        provenance[key]={"route":"approved_exact_qa" if hit else "baseline_passthrough",
                         "source_id":hit["source_id"] if hit else None}
        keyword_after[key]=score(output_after[key],case)
    quality=gate_quality_report({"answers":{"before":output_before,"after":output_after}},cases)
    new=[case["id"] for case in cases if case["group"]=="new"]
    result={"mode":"isolated_approved_qa_overlay","model_weights_updated":False,
        "production_memory_updated":False,"quality_pass":quality["pass"],
        "new_accuracy":sum(keyword_after[k] for k in new)/len(new) if new else None,
        "response_quality_v0633":quality,
        "answers":{"before":output_before,"after":output_after},
        "provenance":provenance,
        "limitations":"Exact question lookup only; simulated overlay, not integrated into chat.py."}
    result["pass"]=bool(quality["pass"] and new and result["new_accuracy"]==1.0)
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--baseline-report",default="results/quality_gate_v0632.json")
    p.add_argument("--cases",default="data/quality_cases_v0632.example.json")
    p.add_argument("--overlay",default="data/semantic_memory_first_v0635.example.jsonl")
    p.add_argument("--output",default="results/semantic_memory_first_v0635.json")
    args=p.parse_args()
    report=json.loads(Path(args.baseline_report).read_text(encoding="utf-8-sig"))
    cases=load_cases(args.cases)
    digest_before=hashlib.sha256(Path(args.baseline_report).read_bytes()).hexdigest()
    result=evaluate(report,cases,load_overlay(args.overlay))
    if hashlib.sha256(Path(args.baseline_report).read_bytes()).hexdigest()!=digest_before:
        raise RuntimeError("baseline report changed")
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"pass":result["pass"],"quality_pass":result["quality_pass"],
      "new_accuracy":result["new_accuracy"],"output":str(out)},ensure_ascii=False))
    raise SystemExit(0 if result["pass"] else 2)
if __name__=="__main__":main()
