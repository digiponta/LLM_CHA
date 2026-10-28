"""v0.13.57 conservative conversation quality release gate.

Runs on v0.13.56 paired raw-generation JSON. Known protected answers
are checked by explicit policy, not by uncalibrated semantic heuristics.
No candidate is promoted by this script: human rating and independent
holdout evidence are separate required gates.
"""
import argparse,hashlib,json
from pathlib import Path

PROTECTED={
    "persona":{"must_contain":["長門有希"],"description":"persona identity"},
    "explanation":{"must_contain_any":["量子力学","微視","物理","重ね合わせ","粒子"],
                   "description":"basic quantum mechanics topicality"},
}
REQUIRED_IDS={"casual","persona","followup","foundation","foundation2","literature","explanation"}

def analyze(data):
    if data.get("version")!="v0.13.56" or data.get("status")!="RAW_GENERATION_COMPARISON":
        raise ValueError("expected v0.13.56 paired raw-generation report")
    rows=data.get("cases")
    if not isinstance(rows,list):raise ValueError("missing cases")
    seen=set();checks=[];hard_fail=[]
    for case in rows:
        cid=case.get("id")
        if not isinstance(cid,str) or cid in seen:raise ValueError("invalid or duplicate case id")
        seen.add(cid)
        outputs=case.get("outputs",{})
        if not all(isinstance(outputs.get(k,{}).get("text"),str) for k in ("base","literature")):
            raise ValueError("paired text missing")
        base=outputs["base"]["text"].strip()
        candidate=outputs["literature"]["text"].strip()
        # Preserve a previously working response when evaluating a regression.
        if base and not candidate:
            checks.append({"id":cid,"check":"nonempty_regression","status":"FAIL",
                           "details":"Base response exists but candidate response is empty"})
            hard_fail.append(cid+":nonempty")
        if cid in PROTECTED:
            rule=PROTECTED[cid]
            def matches(text):
                if "must_contain" in rule:return all(x in text for x in rule["must_contain"])
                return any(x in text for x in rule["must_contain_any"])
            passed_base=matches(base);passed_new=matches(candidate)
            status="FAIL" if passed_base and not passed_new else ("PASS" if passed_new else "INCONCLUSIVE")
            checks.append({"id":cid,"check":"protected_capability",
                           "status":status,"base_match":passed_base,"candidate_match":passed_new,
                           "policy":rule["description"]})
            if status=="FAIL":hard_fail.append(cid+":protected")
    missing=sorted(REQUIRED_IDS-seen)
    if missing:hard_fail.append("missing_required_cases")
    return {"version":"v0.13.57",
            "status":"REJECT" if hard_fail else "HOLD_FOR_HUMAN_AND_HOLDOUT",
            "candidate":"literature",
            "source_comparison_version":"v0.13.56",
            "required_cases":sorted(REQUIRED_IDS),
            "missing_cases":missing,
            "checks":checks,
            "hard_failures":hard_fail,
            "human_review_complete":False,
            "independent_holdout_verified":False,
            "production_promotion_allowed":False,
            "limitations":[
                "Protected answer keywords are explicit smoke tests, not a semantic correctness metric.",
                "No conclusion about all conversations from seven raw-model samples.",
                "LLM_CHA end-to-end gates, memory and retrieval are not evaluated.",
                "Human scores and independent heldout assessment are mandatory for promotion."]}

def write_report(source,output):
    if output.exists():raise FileExistsError("refusing overwrite")
    if source.resolve()==output.resolve():raise ValueError("cannot overwrite input")
    data=json.loads(source.read_text(encoding="utf-8-sig"))
    result=analyze(data)
    result["source_sha256"]=hashlib.sha256(source.read_bytes()).hexdigest()
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("x",encoding="utf-8") as f:
        json.dump(result,f,ensure_ascii=False,indent=2)
        f.write("\n")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--comparison",type=Path,default=Path("results/generation_comparison_v01356.json"))
    p.add_argument("--output",type=Path,default=Path("results/conversation_quality_gate_v01357.json"))
    a=p.parse_args()
    if not a.comparison.is_file():p.error(f"missing report: {a.comparison}")
    r=write_report(a.comparison,a.output)
    print(json.dumps({"status":r["status"],"hard_failures":r["hard_failures"],
                      "human_review_complete":False,
                      "production_promotion_allowed":False},ensure_ascii=False))
    print("report:",a.output)
if __name__=="__main__":main()
