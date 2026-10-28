"""v0.13.58.28: transparent, read-only raw-generation failure audit.

Heuristic classifications are diagnostic flags, NOT semantic entailment,
accuracy proof, independent human review, or promotion authorization.
"""
import argparse,collections,hashlib,json,re
from pathlib import Path

EXPECTED={
 "identity":{"required_any":["長門有希"]},
 "persona_name":{"required_any":["長門","読書","本","情報統合"]},
 "greeting":{"required_any":["こんにちは","どうしました","よろしく"]},
 "tired":{"required_any":["休","疲","無理","お疲れ"]},
 "talk":{"required_any":["話","何","どう","聞","いいよ"]},
 "quantum":{"required_any":["量子","微視","重ね合わせ","測定"]},
 "cpu":{"required_any":["CPU","中央処理","演算","命令","プロセッサ"]},
 "literature":{"required_any":["猫","夏目","漱石","吾輩"]},
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def repetition(text):
    # Detect long runs and repeated spans without external dependencies.
    if re.search(r"(.{2,12})\1{2,}",text):return True
    phrases=re.findall(r"[\u3040-\u30ff\u3400-\u9fff]{3,}",text)
    return any(text.count(s)>=3 for s in phrases if len(s)>=4 and len(s)<=12)

def audit_item(item):
    qid=item["id"];answer=item["raw_answer"].strip()
    if qid not in EXPECTED:raise ValueError("unexpected probe "+qid)
    flags=[]
    if not answer:flags.append("EMPTY_RESPONSE")
    if not item.get("eos_reached",False):flags.append("NO_EOS_WITHIN_BUDGET")
    if "人: " in answer or "\nAI:" in answer:flags.append("ROLE_DELIMITER_LEAK")
    if repetition(answer):flags.append("REPETITION_PATTERN")
    required=EXPECTED[qid]["required_any"]
    if not any(term in answer for term in required):flags.append("MISSING_EXPECTED_CONCEPT")
    if qid=="identity" and answer!="長門有希。":flags.append("IDENTITY_VARIANT_REVIEW")
    return {"id":qid,"category":item.get("category"),"flags":flags,
            "flagged":bool(flags),"answer":answer,
            "generated_tokens":item.get("generated_tokens"),
            "eos_reached":bool(item.get("eos_reached"))}

def audit(source,output):
    if output.exists():raise FileExistsError(output)
    data=json.loads(source.read_text(encoding="utf-8-sig"))
    if data.get("version")!="v0.13.58.27" or data.get("status")!="RAW_GENERATION_DIAGNOSTIC":
        raise ValueError("unexpected source version/status")
    probes=data.get("probes",[])
    expected_ids=set(EXPECTED)
    if len(probes)!=len(expected_ids) or set(x["id"] for x in probes)!=expected_ids:
        raise ValueError("unexpected probe set")
    results={};counts={}
    for arm in ("Base","W","WR","WRP"):
        items=data["results"][arm]
        if len(items)!=len(expected_ids) or set(i["id"] for i in items)!=expected_ids:
            raise ValueError("missing/duplicate probe results: "+arm)
        byid={x["id"]:x for x in items}
        if any(byid[p["id"]].get("user")!=p["user"] for p in probes):
            raise ValueError("prompt changed in result: "+arm)
        audited=[audit_item(byid[p["id"]]) for p in probes]
        results[arm]=audited
        c=collections.Counter(flag for entry in audited for flag in entry["flags"])
        counts[arm]={"flagged_probes":sum(entry["flagged"] for entry in audited),
                     "total_probes":len(audited),"flag_counts":dict(c),
                     "clean_heuristic_probes":sum(not entry["flagged"] for entry in audited)}
    report={"version":"v0.13.58.28","status":"HEURISTIC_AUDIT_COMPLETE",
            "source_sha256":sha(source),"probe_ids":[p["id"] for p in probes],
            "results":results,"summary":counts,
            "semantic_consistency_verified":False,"human_quality_approved":False,
            "independent_holdout_verified":False,"training_performed":False,
            "production_promotion_allowed":False,
            "limitations":["Keyword matching cannot establish correctness or meaningful relevance.",
                           "A clean heuristic probe does not imply a good answer.",
                           "No generation, learning, retrieval or semantic memory use occurs."]}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("results/jawiki_generation_v0135827.json"))
    p.add_argument("--output",type=Path,default=Path("results/jawiki_failure_audit_v0135828.json"))
    a=p.parse_args();r=audit(a.source,a.output)
    print(json.dumps({"status":r["status"],"summary":r["summary"]},ensure_ascii=False))
    print("report:",a.output)
if __name__=="__main__":main()
