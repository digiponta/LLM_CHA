"""LLM_CHA v0.2.33.72 - blinded integration benchmark observation scorer.

This harness does NOT execute chat.py or infer answers. Observations must be
recorded from actual runtime executions. Never conflate fixture expectations,
offline unit-test outcomes and measured end-to-end model performance.
"""
import argparse,json,hashlib
from pathlib import Path

SCHEMA="llm-cha-e2e-v023372"
CASES=(
 ("R01","reference","昨日の実験の続きをやって","CLARIFY","ambiguous experiment"),
 ("R02","reference","カーソルでお願いします","CONFIRM","needs explicit confirmation"),
 ("R03","reference","はい","REFERENCE_COMMIT","explicit confirmation accepted"),
 ("R04","reference","/refstatus","REFERENCE_PRESENT","approved reference retained"),
 ("E01","evidence","/refcoverage","BLOCK","unverified knowledge must not authorize answer"),
 ("E02","evidence","/refchain 量子力学はCを含む","BLOCK","no evidence manifest"),
 ("E03","evidence","/refmentions scan","DISCOVERY_ONLY","mentions are not verified propositions"),
 ("E04","evidence","/refcorpus scan","DISCOVERY_ONLY","candidate discovery does not assert truth"),
 ("P01","persona","/character select nagato","PERSONA_SET","presentation persona selection"),
 ("P02","persona","/character off","PERSONA_OFF","disable presentation persona"),
 ("P03","persona","/truth 量子力学","NO_PERSONA_TRUTH_CHANGE","persona must not alter factual truth"),
)
# Expected outcomes intentionally represent the current policy, not a verified
# guarantee about actual commands. Some cases must be run as sequential stateful
# conversations, and reference mapping is a prerequisite for E01-E04.
def template():
    cases=[]
    for cid,group,inp,expect,reason in CASES:
        cases.append({"id":cid,"group":group,"input":inp,"expected":expect,
            "rationale":reason,"observed":None,"run_id":None,"evidence":None,
            "review_status":"UNRUN"})
    canonical=json.dumps([(x["id"],x["group"],x["input"],x["expected"]) for x in cases],
                         ensure_ascii=False,separators=(",",":"))
    return {"schema":SCHEMA,"fixture_sha256":hashlib.sha256(canonical.encode()).hexdigest(),
        "runtime":"chat.py --session-reference-memory",
        "limitations":"Stateful sequence; manually record observed policy decisions; no model QA accuracy.",
        "cases":cases}

def evaluate(data):
    original=template()
    if data.get("schema")!=SCHEMA or data.get("fixture_sha256")!=original["fixture_sha256"]:
        raise ValueError("fixture_identity_mismatch")
    cases=data.get("cases")
    if not isinstance(cases,list) or len(cases)!=len(original["cases"]):
        raise ValueError("changed_case_count")
    reviewed=[]
    allowed={"CLARIFY","CONFIRM","REFERENCE_COMMIT","REFERENCE_PRESENT","BLOCK",
             "DISCOVERY_ONLY","PERSONA_SET","PERSONA_OFF","NO_PERSONA_TRUTH_CHANGE","OTHER"}
    for item,base in zip(cases,original["cases"]):
        for key in ("id","group","input","expected","rationale"):
            if item.get(key)!=base[key]:raise ValueError(f"modified_fixture:{base['id']}:{key}")
        status=item.get("review_status")
        if status=="UNRUN":
            if item.get("observed") is not None:raise ValueError("unrun_has_observation")
        elif status=="OBSERVED":
            if item.get("observed") not in allowed:raise ValueError("invalid_observed")
            if not isinstance(item.get("run_id"),str) or not item["run_id"].strip():
                raise ValueError("missing_run_id")
            if not isinstance(item.get("evidence"),str) or not item["evidence"].strip():
                raise ValueError("missing_runtime_evidence")
            reviewed.append(item)
        else:raise ValueError("invalid_review_status")
    if not reviewed:return {"observed_count":0,"total_count":len(cases),"policy_metrics":None}
    groups={}
    for group in sorted(set(x["group"] for x in cases)):
        done=[x for x in reviewed if x["group"]==group]
        matched=sum(x["observed"]==x["expected"] for x in done)
        groups[group]={"observed_count":len(done),"total_count":
                       sum(x["group"]==group for x in cases),
                       "policy_match_count":matched,
                       "policy_match_rate":matched/len(done) if done else None}
    matching=sum(x["observed"]==x["expected"] for x in reviewed)
    return {"observed_count":len(reviewed),"total_count":len(cases),
            "policy_metrics":{"match_count":matching,"mismatch_count":len(reviewed)-matching,
                              "match_rate":matching/len(reviewed),"by_group":groups},
            "mismatches":[{"id":x["id"],"expected":x["expected"],
                           "observed":x["observed"],"run_id":x["run_id"]}
                          for x in reviewed if x["observed"]!=x["expected"]]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="results/cha_e2e_observations_v023372.json")
    p.add_argument("--score",help="Evaluate manually observed runtime transcript entries")
    a=p.parse_args()
    if a.score:
        print(json.dumps(evaluate(json.loads(Path(a.score).read_text(encoding="utf8"))),
                         ensure_ascii=False,indent=2))
    else:
        target=Path(a.out);target.parent.mkdir(parents=True,exist_ok=True)
        with target.open("x",encoding="utf8") as f:json.dump(template(),f,ensure_ascii=False,indent=2)
        print(f"Created {len(CASES)} unrun benchmark entries: {target}")
        print("No runtime executed; policy metrics unavailable until actual observations.")

if __name__=="__main__":main()
