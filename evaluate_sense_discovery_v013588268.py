"""Offline-only review queue report; no candidate approvals or writes to live knowledge."""
import argparse,json
from pathlib import Path
from evidence_sense_discovery_v013588268 import inspect_snapshot

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data",default="data/wiki_evidence_review_v013588260.json")
    p.add_argument("--output",default="results/sense_discovery_v013588268.json")
    a=p.parse_args()
    data=json.loads(Path(a.data).read_text(encoding="utf-8-sig"))
    report=inspect_snapshot(data)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"candidate_count":report["candidate_count"],
                      "approved_count":0,"report":str(out)},ensure_ascii=False))

if __name__=="__main__":
    main()
