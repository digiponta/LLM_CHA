"""RSE diagnostic candidate acceptance with conservative structural safeguards.

ACCEPT_CANDIDATE means eligible for subsequent evaluation, NOT an approved live reply.
"""
import argparse,json,re
from pathlib import Path
from rse_selection_gate_v013588304 import gate

SAFE_INTENTS={"CHAT_INVITATION","GREETING"}
UNSAFE_SELF_REPORT=re.compile(r"(私|僕|俺|うち|家族|実家|学校|住ん|昨日|今日.*行|元気です|食べ|飲ん|仕事|病気|疲れ)")
def assess(question,source_question,source_answer):
    original=gate(question,source_question,source_answer)
    reasons=list(original["reasons"])
    ans=source_answer.strip()
    if not ans or len(ans)>120:reasons.append("RESPONSE_LENGTH_INVALID")
    if UNSAFE_SELF_REPORT.search(ans):reasons.append("SELF_REPORT_RISK")
    if original["status"]=="REJECT" or reasons:
        status="REJECT"
    elif original["question_intent"] not in SAFE_INTENTS:
        status="MANUAL_REVIEW_REQUIRED"
        reasons.append("INTENT_NOT_APPROVED_FOR_CANDIDATE")
    elif re.search(r"(？|\?)",ans) and len(ans)<4:
        status="MANUAL_REVIEW_REQUIRED"
        reasons.append("INSUFFICIENT_RESPONSE")
    else:
        status="ACCEPT_CANDIDATE"
    return {"status":status,"reasons":sorted(set(reasons)),
            "intent":original["question_intent"],"auto_reply":False,
            "verified_semantic_relevance":False,"generation_or_expansion_enabled":False}

def benchmark(cases):
    out=[]
    for x in cases:
        result=assess(x["query"],x["source_question"],x["source_answer"])
        out.append({"id":x["id"],"label_suitable":x["suitable"],**result})
    npos=sum(x["label_suitable"] is True for x in out)
    nneg=sum(x["label_suitable"] is False for x in out)
    tp=sum(x["label_suitable"] is True and x["status"]=="ACCEPT_CANDIDATE" for x in out)
    fp=sum(x["label_suitable"] is False and x["status"]=="ACCEPT_CANDIDATE" for x in out)
    return {"status":"DEVELOPMENT_EVALUATION_ONLY","cases":len(out),"positive":npos,"negative":nneg,
            "candidate_accept_precision":tp/(tp+fp) if tp+fp else None,
            "candidate_accept_recall":tp/npos if npos else None,
            "false_accept_count":fp,"accept_candidate_count":tp+fp,
            "independent_holdout":False,"human_labels_verified":False,
            "live_auto_accept_enabled":False,"rows":out}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--cases",default="data/rse_accept_development_v013588307.json")
    p.add_argument("--output",default="results/rse_accept_development_v013588307.json")
    a=p.parse_args()
    cases=json.loads(Path(a.cases).read_text(encoding="utf-8-sig"))["cases"]
    result=benchmark(cases)
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="rows"},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
