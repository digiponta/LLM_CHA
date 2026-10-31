"""AI-delegated advisory review without falsely claiming human approval.

Reads existing quality candidates, emits per-candidate, attributable decisions.
No change to production Semantic Memory, and does not forge human_review_recorded.
"""
import argparse,json
from pathlib import Path

REVIEWS={
 "ビッグバン":("DEFER","爆発的膨張の比喩が誤解を招く余地がある。原文・定義の再確認が必要。"),
 "閃亜鉛鉱":("RECOMMEND_APPROVE","亜鉛の硫化鉱物という記述は定義文として整合的。独立した真実性検証は未実施。"),
 "量子力学":("RECOMMEND_APPROVE_WITH_CAUTION","現代物理学の理論・分野としての説明は妥当だが、物理理論の内容の説明としては不十分。"),
 "光電効果":("RECOMMEND_APPROVE_WITH_CAUTION","光照射に伴う電子放出・電流についての概要として妥当。光電効果の分類を確認する余地がある。")
}

def delegate_review(report):
    rows=[]
    for c in report.get("candidates",[]):
        decision,note=REVIEWS.get(c.get("subject"),("DEFER","未評価のSubject。"))
        rows.append({"candidate_id":c.get("id"),"subject":c.get("subject"),
                     "meaning":c.get("meaning"),"evidence_sentence":c.get("evidence_sentence"),
                     "source_url":c.get("source_url"),
                     "decision":decision,"reviewer_type":"AI_DELEGATE",
                     "reviewer":"ChatGPT (AI delegated review)","note":note,
                     "source_trust":"EXTERNAL_UNVERIFIED",
                     "human_review_recorded":False,"approved":False,
                     "production_promoted":False})
    return {"status":"AI_DELEGATED_REVIEW_RECORDED","records":rows,
            "record_count":len(rows),"human_approved_count":0,
            "production_changed":False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--quality",default="results/sense_definition_quality_v013588270.json")
    p.add_argument("--output",default="results/sense_ai_delegated_review_v013588275.json")
    a=p.parse_args()
    report=json.loads(Path(a.quality).read_text(encoding="utf-8-sig"))
    result=delegate_review(report)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"records":result["record_count"],
                      "human_approved":result["human_approved_count"],
                      "production_changed":False,"output":str(out)},ensure_ascii=False))
if __name__=="__main__":main()
