"""v0.13.12: conservative, explicit checkpoint promotion.

Default preflight only. --promote requires a passing assessment and creates
timestamp-free .pre-v01312 backup files. Never updates knowledge approvals.
"""
import argparse
import json
import shutil
from pathlib import Path

def assess(report, base, candidate, state):
    reasons=[]
    if not base.exists(): reasons.append("BASE_MISSING")
    if not candidate.exists(): reasons.append("CANDIDATE_MISSING")
    if not state.exists(): reasons.append("PILOT_STATE_MISSING")
    if report.get("promoted") is not False: reasons.append("REPORT_NOT_CANDIDATE")
    if report.get("pilot_count",0)<1: reasons.append("NO_PILOT_EXAMPLES")
    pilot=report.get("pilot_fit",{})
    stability=report.get("stability_retention",{})
    if pilot.get("delta_nll") is None or pilot["delta_nll"]>=0:
        reasons.append("PILOT_NOT_IMPROVED")
    if stability.get("delta_nll") is None or stability["delta_nll"]>0.05:
        reasons.append("STABILITY_REGRESSION_OR_MISSING")
    if report.get("candidate_fingerprint_count",0)<=report.get("base_fingerprint_count",0):
        reasons.append("NO_NEW_FINGERPRINTS")
    return reasons

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--report",type=Path,default=Path("results/unapproved_checkpoint_comparison_v01311.json"))
    p.add_argument("--base",type=Path,default=Path("model/model-gpu-v1.6.2-online.pt"))
    p.add_argument("--candidate",type=Path,default=Path("model/model-gpu-v1.6.2-unapproved-pilot-v01310.pt"))
    p.add_argument("--pilot-state",type=Path,default=Path("results/unapproved_pilot_state_v01310.json"))
    p.add_argument("--production-state",type=Path,default=Path("data/chat_learning_state.json"))
    p.add_argument("--promote",action="store_true")
    args=p.parse_args()
    if not args.report.exists():p.error("comparison report missing")
    report=json.loads(args.report.read_text(encoding="utf-8-sig"))
    reasons=assess(report,args.base,args.candidate,args.pilot_state)
    if args.base.resolve()==args.candidate.resolve():reasons.append("IDENTICAL_INPUT_OUTPUT")
    if args.production_state.resolve()==args.pilot_state.resolve():reasons.append("IDENTICAL_STATE")
    # This tool does not validate generative behavior, provenance, or approval
    # binding. These require separate runtime review.
    if args.promote:reasons.append("GENERATION_AND_PROVENANCE_REVIEW_NOT_IMPLEMENTED")
    outcome={"status":"BLOCKED" if reasons else "PREFLIGHT_PASS",
             "reasons":reasons,"promotion_executed":False,
             "production_model":str(args.base),"candidate_model":str(args.candidate),
             "requires":"independent generation, truth-state and provenance review"}
    print(json.dumps(outcome,ensure_ascii=False,indent=2))
    if reasons:raise SystemExit(2)

if __name__=="__main__":main()
