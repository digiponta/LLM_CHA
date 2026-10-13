"""v0.4.2 read-only persona concept coverage diagnostic.

Reports corpus and component-level retrieval evidence; does not predict the
complete chat.py dispatcher or alter any truth/learning state.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from persona_semantic_memory_v0371 import evidence
from persona_routing_v0374 import ranked_persona_reply
from persona_normalized_means_v0377 import normalized_rows

DEFAULT_CONCEPTS=("数学","量子力学","文学","小説")

def inspect(source, concepts=DEFAULT_CONCEPTS):
    source=Path(source)
    means=normalized_rows(source)
    result=[]
    for concept in concepts:
        hits=evidence(source,concept,limit=30)
        response,ranked=ranked_persona_reply(source,concept)
        roles=[r for r in means if concept in (r["subject"],r["means"])]
        result.append({
            "concept":concept,"raw_evidence_count_capped_30":len(hits),
            "raw_evidence_capped":len(hits)==30,
            "raw_evidence_present":bool(hits),
            "ranked_persona_available":response is not None,
            "ranked_selected":[{"line":x.line,"segment":x.segment,
                                "excerpt":x.excerpt,"factual_truth":x.factual_truth}
                               for x in ranked],
            "means_role_candidate_count":len(roles),
            "means_role_lines":[r["line"] for r in roles],
            "runtime_truth_state":"NOT_PROBED",
            "runtime_route":"NOT_PROBED",
            "interpretation":("corpus evidence exists; if chat returns UNKNOWN, "
                              "inspect dispatcher/route priority and truth state"
                              if hits else
                              "no literal excerpt found in this corpus; check other knowledge sources")
        })
    return {"version":"v0.4.2","source":str(source),
            "source_line_count":len(source.read_text(encoding="utf-8-sig").splitlines()),
            "model_training_performed":False,"truth_gate_modified":False,
            "runtime_route_measured":False,"concepts":result}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--corpus",default="data/data-nagato.txt")
    p.add_argument("--report",default="results/persona_concept_coverage_v0402.json")
    p.add_argument("--concept",action="append",dest="concepts")
    a=p.parse_args()
    report=inspect(a.corpus,a.concepts or DEFAULT_CONCEPTS)
    target=Path(a.report);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    for row in report["concepts"]:
        print(f'{row["concept"]}: raw={row["raw_evidence_count_capped_30"]}, '
              f'ranked={row["ranked_persona_available"]}, '
              f'means_candidates={row["means_role_candidate_count"]}, '
              f'runtime=NOT_PROBED')
    print("report:",target)
if __name__=="__main__":main()
