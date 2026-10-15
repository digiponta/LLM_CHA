"""v0.5.38 read-only diagnosis of coverage gaps in Japanese proposition extraction."""
import re
from collections import Counter
from wiki_proposition_comparison_v0537 import collect

def diagnose_body(body,source=None,sample_limit=5):
    if not isinstance(body,str):return {"status":"INVALID_BODY","counts":{},"samples":[]}
    counts=Counter();samples=[]
    for raw in re.split(r"[。\n]",body):
        s=raw.strip()
        if not s:continue
        counts["sentences"]+=1
        if not 12<=len(s)<=240:
            reason="LENGTH_OUT_OF_RANGE"
        elif collect(s+"。",source):
            reason="EXTRACTED"
            counts["propositions"]+=len(collect(s+"。",source))
        elif "は" not in s and "とは" not in s:
            reason="SUBJECT_OR_COPULA_NOT_RECOGNIZED"
        elif any(x in s for x in ("による","に含まれる","できる","として")):
            reason="UNSUPPORTED_GRAMMAR"
        elif any(x in s for x in ("、","および","また","一方")):
            reason="COMPLEX_CLAUSE"
        else:
            reason="UNSUPPORTED_PATTERN"
        counts[reason]+=1
        if reason!="EXTRACTED" and len(samples)<sample_limit:
            samples.append({"reason":reason,"excerpt":s[:140],"source":source})
    counts["unextracted_sentences"]=counts["sentences"]-counts["EXTRACTED"]
    return {"status":"DIAGNOSTIC_COMPLETE","counts":dict(counts),"samples":samples,
            "diagnostic_only":True,"verified":False,"train_ready":False}

def summarize(multi_evidence):
    if not isinstance(multi_evidence,dict) or multi_evidence.get("status")!="EVIDENCE_COLLECTED":
        return {"status":"NO_EVIDENCE"}
    stats=Counter(p.get("status","INSUFFICIENT") for p in multi_evidence.get("comparison",[]))
    articles=multi_evidence.get("articles",[])
    return {"status":"COMPARISON_DIAGNOSTIC","articles":len(articles),
            "propositions":len(multi_evidence.get("propositions",[])),
            "comparison_counts":{k:stats[k] for k in ("MATCH","CONFLICT","COMPLEMENT","INSUFFICIENT")},
            "diagnostic_only":True,"causal_answer_approved":False}
