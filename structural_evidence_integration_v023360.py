"""v0.2.33.60 isolated positive/negative structural evidence integration.

Uses actual SessionReferenceStore, VerifiedConceptMapping and StructuralReferenceBridge;
the semantic facade is replaced by a deterministic, isolated fixture. No changes to
the user's factual Semantic Memory, truth records, model weights, or /sleep.
"""
import argparse,json,tempfile
from pathlib import Path
from types import SimpleNamespace
from runtime_reference_integration_v023352 import SessionReferenceStore,RuntimeReferenceBridge
from verified_reference_concept_v023356 import VerifiedConceptMapping
from structural_semantic_consistency_v023359 import StructuralReferenceBridge

def semantic_fixture(evidence,answer,truth="TRUE",state="KNOWN",action="ANSWER"):
    return SimpleNamespace(state=state,truth_state=truth,action=action,answer=answer,
        provenance=SimpleNamespace(source="isolated-reviewed-fixture",origin="v023360-local-only",
                                   evidence=evidence,retrieval_priority=0))
class IsolatedSemanticFacade:
    def __init__(self,result):self.result=result;self.queries=[]
    def resolve(self,query):
        self.queries.append(query)
        return self.result

CASES=[
    ("matching_is_a","AはBである","AはBである","TRUE","KNOWN","structural_match","exact_structural_match"),
    ("matching_includes","AはBを含む","AはBを含む","TRUE","KNOWN","structural_match","exact_structural_match"),
    ("matching_conditional","条件XではAはBである","条件XではAはBである","TRUE","KNOWN","structural_match","exact_structural_match"),
    ("negative_polarity","GPUは並列計算に適する","GPUは並列計算に適さない","TRUE","KNOWN","structural_blocked","polarity_mismatch"),
    ("reverse_relation","AはBを含む","BはAを含む","TRUE","KNOWN","structural_blocked","argument_mismatch"),
    ("missing_condition","条件XではAはBである","AはBである","TRUE","KNOWN","structural_blocked","condition_mismatch"),
    ("unverified","GPUは並列計算に適する","GPUは並列計算に適する","UNVERIFIED","KNOWN","structural_blocked","truth_not_true"),
    ("raw_corpus","GPUは並列計算に適する","GPUは並列計算に適する","TRUE","RAW_CORPUS_ONLY","structural_blocked","knowledge_not_validated"),
    ("unsupported_language","GPUは速い","GPUは速い","TRUE","KNOWN","structural_blocked","unsupported_grammar"),
]
def evaluate():
    rows=[]
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        refs=SessionReferenceStore(root/"references.sqlite3")
        runtime=RuntimeReferenceBridge(refs)
        for utterance in ("昨日の実験の続きをやって","cursor","はい"):
            runtime.receive(utterance,"isolated-test")
        mappings=VerifiedConceptMapping(root/"mappings.sqlite3")
        token=mappings.propose("isolated-test","cursor","GPU","local-fixture-only")
        if not mappings.approve("isolated-test",token):
            raise RuntimeError("Mapping approval failed")
        for name,evidence,answer,truth,state,status,reason in CASES:
            facade=IsolatedSemanticFacade(semantic_fixture(evidence,answer,truth,state))
            bridge=StructuralReferenceBridge(refs,mappings,facade)
            r=bridge.lookup("isolated-test")
            ok=(r["status"]==status and r["reason"]==reason
                and facade.queries==["GPUとは"]
                and (bool(r["answer"])==(status=="structural_match")))
            rows.append({"case":name,"passed":ok,"expected_status":status,
                        "actual_status":r["status"],"expected_reason":reason,
                        "actual_reason":r["reason"],"query":facade.queries})
        # Approval gates must suppress calls to the semantic layer.
        no_ref=IsolatedSemanticFacade(semantic_fixture("AはBである","AはBである"))
        wrong=StructuralReferenceBridge(refs,mappings,no_ref).lookup("different-session")
        rows.append({"case":"cross_context","passed":wrong["status"]=="no_approved_reference" and not no_ref.queries,
                     "actual_status":wrong["status"]})
        mappings.invalidate("isolated-test","cursor")
        no_mapping=IsolatedSemanticFacade(semantic_fixture("AはBである","AはBである"))
        blocked=StructuralReferenceBridge(refs,mappings,no_mapping).lookup("isolated-test")
        rows.append({"case":"mapping_invalidation","passed":blocked["status"]=="no_approved_mapping" and not no_mapping.queries,
                     "actual_status":blocked["status"]})
    return {"version":"v0.2.33.60","passed":sum(x["passed"] for x in rows),"total":len(rows),
            "cases":rows,"scope":"Isolated semantic-result fixtures; actual SQLite reference/mapping and structural gate",
            "production_semantic_memory_changed":False,"model_training":False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="results/structural_evidence_integration_v023360.json")
    a=p.parse_args()
    report=evaluate()
    out=Path(a.out)
    if out.exists():raise FileExistsError("Refusing to overwrite existing report: "+str(out))
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"LLM_CHA v0.2.33.60: {report['passed']}/{report['total']} PASS")
    for row in report["cases"]:
        print(f"{'PASS' if row['passed'] else 'FAIL'} {row['case']} ({row['actual_status']})")
    print("Saved:",out)
    if report["passed"]!=report["total"]:raise SystemExit(1)
if __name__=="__main__":main()
