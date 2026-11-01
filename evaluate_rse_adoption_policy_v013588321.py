"""Apply experimental policy to an existing real-transcript comparison report."""
import argparse,json
from pathlib import Path
from rse_adoption_policy_v013588321 import evaluate_transcript_comparison
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--comparison",default="results/rse_live_transcript_shadow_v013588320.json")
 p.add_argument("--output",default="results/rse_adoption_policy_v013588321.json")
 a=p.parse_args()
 report=json.loads(Path(a.comparison).read_text(encoding="utf-8-sig"))
 if report.get("status")!="REAL_TRANSCRIPT_SHADOW_COMPARISON":raise SystemExit("INVALID_COMPARISON_REPORT")
 result=evaluate_transcript_comparison(report)
 dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
 dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
