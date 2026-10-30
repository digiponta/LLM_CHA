"""Offline comparison of strict gate vs extractive evidence fallback using saved reports."""
import argparse
import json
from pathlib import Path
from evidence_guided_decoding_v013588254 import evaluate_decoding

def benchmark(evidence,reports):
    if evidence.get("status")!="EVIDENCE":raise ValueError("EVIDENCE_REQUIRED")
    entries=[]
    for name,report in reports.items():
        for model_name in ("base","candidate"):
            case=report.get(model_name,{})
            if "text" not in case:continue
            decision=evaluate_decoding(case["text"],evidence)
            entries.append({"experiment":name,"model":model_name,
                "raw_gate":decision["raw_gate"],"strategy":decision["strategy"],
                "selected_gate":decision["gate"],
                "raw_candidate":case["text"],
                "answer":decision["answer"]})
    return {"status":"OFFLINE_EXTRACTIVE_DECODING_COMPARISON",
            "cases":len(entries),"cases_detail":entries,
            "production_changed":False,
            "note":"Extractive fallback is copied source text, not independent evidence validation. No new LLM generation."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--evidence-json",default="results/evidence_snapshot_v013588249.json")
    p.add_argument("--report",action="append",required=True,help="name=path-to-report.json")
    p.add_argument("--output",default="results/evidence_decoding_v013588254.json")
    a=p.parse_args()
    evidence=json.loads(Path(a.evidence_json).read_text(encoding="utf-8-sig"))
    reports={}
    for item in a.report:
        name,sep,path=item.partition("=")
        if not sep or not name or not path:raise ValueError("EXPECTED_NAME_EQUALS_PATH")
        reports[name]=json.loads(Path(path).read_text(encoding="utf-8-sig"))
    result=benchmark(evidence,reports)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"cases":result["cases"],
        "strategies":{f"{x['experiment']}/{x['model']}":x["strategy"] for x in result["cases_detail"]},
        "report":str(out),"production_changed":False},ensure_ascii=False))
if __name__=="__main__":main()
