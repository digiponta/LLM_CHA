"""v0.4.5 read-only conservative Persona evidence relevance assessment.

Heuristic features measure textual support, not semantic correctness or truth.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from persona_semantic_memory_v0371 import evidence

def classify(excerpt: str, concept: str):
    # Japanese particles determine whether the focus is a syntactic topic
    # or is mentioned as an object, qualifier, or secondary term.
    topic=bool(re.search(r"(?:^|[、，\s])"+re.escape(concept)+r"(?:は|とは|が|という)",excerpt))
    definition=bool(re.search(re.escape(concept)+r"(?:とは|は)[^。]{0,90}(?:である|を指す|のこと|と定義される)",excerpt))
    secondary=concept in excerpt and not topic
    length=len(excerpt.strip())
    complete=length>=12 and not excerpt.rstrip().endswith(("、","，","は","が","の"))
    return {"subject_match":topic,"definition_pattern":definition,
            "secondary_mention":secondary,"fragment_complete_heuristic":complete,
            "predicate_cue":bool(re.search(r"(?:する|である|いる|なる|分類|含む|表現)",excerpt)),
            "context_verified":False}

def inspect(source: str | Path, concepts=("数学","量子力学","文学","小説")):
    output=[]
    for concept in concepts:
        entries=evidence(source,concept,limit=30)
        rated=[]
        for row in entries:
            f=classify(row.excerpt,concept)
            # Transparent ordering only, not a calibrated confidence score.
            score=3*int(f["definition_pattern"])+2*int(f["subject_match"])+int(f["predicate_cue"])+int(f["fragment_complete_heuristic"])
            rated.append({"id":row.id,"line":row.line,"segment":row.segment,
                          "excerpt":row.excerpt,"features":f,"heuristic_score":score,
                          "factual_truth":"NOT_ASSESSED"})
        rated.sort(key=lambda x:(-x["heuristic_score"],x["line"],x["segment"]))
        output.append({"concept":concept,"candidate_count_capped_30":len(entries),
                       "top_candidates":rated[:5],
                       "definition_supported_by_human_review":False,
                       "evaluation_type":"UNVALIDATED_HEURISTIC"})
    return {"version":"v0.4.5","source":str(source),"runtime_enabled":False,
            "truth_gate_modified":False,"human_relevance_reviewed":0,
            "concepts":output}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--corpus",default="data/data-nagato.txt")
    p.add_argument("--report",default="results/persona_evidence_relevance_v0405.json")
    p.add_argument("--concept",action="append",dest="concepts")
    a=p.parse_args()
    result=inspect(a.corpus,a.concepts or ("数学","量子力学","文学","小説"))
    out=Path(a.report);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    for row in result["concepts"]:
        top=row["top_candidates"][0] if row["top_candidates"] else None
        print(f'{row["concept"]}: candidates={row["candidate_count_capped_30"]} '
              f'top_score={top["heuristic_score"] if top else "N/A"} '
              f'top_subject={top["features"]["subject_match"] if top else "N/A"}')
    print("report:",out)
if __name__=="__main__":main()
