"""v0.3.7.6: conservative persona means-role evidence extraction and corpus audit.

Read-only, no scientific truth promotion. Unsupported predicates are kept as
role candidates, never rendered as causative claims.
"""
from __future__ import annotations
from pathlib import Path
import argparse
import json
import re
from means_centric_semantics_v0372 import transform
from persona_semantic_memory_v0371 import segments

PATTERNS=(
    ("によって",re.compile(r"^(?P<subject>[^、。]{1,40})は、?(?P<means>[^、。]{1,40})によって、?(?P<predicate>[^、。]{2,100})$")),
    ("を使って",re.compile(r"^(?P<subject>[^、。]{1,40})は、?(?P<means>[^、。]{1,40})を使って、?(?P<predicate>[^、。]{2,100})$")),
    ("を通じて",re.compile(r"^(?P<subject>[^、。]{1,40})は、?(?P<means>[^、。]{1,40})を通じて、?(?P<predicate>[^、。]{2,100})$")),
)
def extract(source):
    source=Path(source)
    rows=[]
    for line_no,line in enumerate(source.read_text(encoding="utf-8-sig").splitlines(),1):
        for segment_no,sentence in enumerate(segments(line),1):
            for marker,pattern in PATTERNS:
                match=pattern.fullmatch(sentence)
                if not match:continue
                subject,means,predicate=(match.group(name).strip() for name in ("subject","means","predicate"))
                if not all((subject,means,predicate)):continue
                # Only verbatim 'によって' + whitelisted predicates permit derived causatives.
                derived=transform(sentence) if marker=="によって" else {"status":"UNSUPPORTED","derived":None}
                rows.append({"subject":subject,"means":means,"predicate":predicate,
                             "marker":marker,"original":sentence,"line":line_no,
                             "segment":segment_no,"source":str(source),
                             "relation":"MEANS_OF","candidate_state":"PERSONA_EVIDENCE",
                             "factual_truth":"NOT_ASSESSED",
                             "derivation_status":derived["status"],"derived":derived["derived"]})
                break
    return rows

def audit(source):
    source=Path(source)
    rows=extract(source)
    counts={marker:sum(row["marker"]==marker for row in rows) for marker,_ in PATTERNS}
    derivable=sum(row["derived"] is not None for row in rows)
    return {"version":"v0.3.7.6","source":str(source),"source_lines":len(source.read_text(encoding="utf-8-sig").splitlines()),
            "candidate_count":len(rows),"causative_derivable":derivable,
            "unrendered_candidates":len(rows)-derivable,"by_marker":counts,
            "factual_promotions":0,"corpus_modified":False,"candidates":rows}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--corpus",default="data/data-nagato.txt")
    p.add_argument("--report",default="results/persona_means_audit_v0376.json")
    args=p.parse_args()
    data=audit(args.corpus)
    target=Path(args.report);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in data.items() if k!="candidates"},ensure_ascii=False,indent=2))
    print("report:",target)
if __name__=="__main__":main()
