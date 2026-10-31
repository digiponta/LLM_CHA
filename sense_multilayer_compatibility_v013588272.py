"""v0.72 cross-layer read-only compatibility; no semantic proof or promotion."""
import argparse,json
from pathlib import Path
from semantic_proposition_v1090 import load_propositions
from subject_keyed_proposition_v1090 import load_subject_index
from typed_subject_proposition_v10100 import load_typed_index
from unified_semantic_bridge_v1090 import load_unified_rows
from truth_state_v10103 import load_truth_records
from sense_semantic_compatibility_v013588271 import compare,normalized

def inspect(candidates,layers):
    rows=[]
    for c in candidates:
        subject=normalized(c.get("subject"))
        per={}
        for layer in ("atomic","subject_index","typed_index","unified"):
            per[layer]=compare(c,layers.get(layer,[]))["status"]
        truth=[x for x in layers.get("truth",[]) if normalized(x.get("subject"))==subject]
        per["truth"]=truth[0]["state"] if truth else "NO_TRUTH_RECORD"
        blocking=per["truth"] in ("REJECTED","DISPUTED","FALSE","REVOKED")
        rows.append({"candidate_id":c.get("id"),"subject":subject,"layers":per,
                     "truth_blocked":blocking,"manual_review_required":True,
                     "approved":False,"production_promoted":False})
    return {"status":"MULTILAYER_SEMANTIC_COMPATIBILITY_DIAGNOSTIC",
            "case_count":len(rows),"rows":rows,"approved_count":0,"production_changed":False,
            "scope":"atomic, subject, typed, unified, truth; internalized weights not inspected",
            "caution":"Lexical comparisons are not proofs of truth, synonymy, or contradiction."}

def load_layers(args):
    return {
      "atomic":[{"subject":x.subject,"value":x.value} for x in load_propositions(Path(args.atomic))],
      "subject_index":[{"subject":x.subject,"value":x.value} for x in load_subject_index(Path(args.subject_index))],
      "typed_index":[{"subject":x.subject,"value":x.value} for x in load_typed_index(Path(args.typed_index))],
      "unified":[{"subject":x.get("concept",""),"value":x.get("assistant","")} for x in load_unified_rows(Path(args.unified))],
      "truth":[{"subject":x.concept,"state":x.state} for x in load_truth_records(Path(args.truth))],
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--candidates",default="results/sense_definition_quality_v013588270.json")
    p.add_argument("--atomic",default="data/semantic_propositions_v1090.jsonl")
    p.add_argument("--subject-index",default="data/subject_keyed_propositions_v1090.jsonl")
    p.add_argument("--typed-index",default="data/typed_subject_propositions_v10100.jsonl")
    p.add_argument("--unified",default="data/unified_semantic_memory_v1090.jsonl")
    p.add_argument("--truth",default="data/truth_state_v10103.jsonl")
    p.add_argument("--output",default="results/sense_multilayer_v013588272.json")
    a=p.parse_args()
    candidates=json.loads(Path(a.candidates).read_text(encoding="utf-8-sig"))["candidates"]
    report=inspect(candidates,load_layers(a))
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"cases":report["case_count"],"approved":0,"report":str(out)},ensure_ascii=False))
if __name__=="__main__":main()
