"""Read-only diagnosis of duplicate copulas in proposition pipelines."""
import argparse,json,re
from pathlib import Path
from semantic_proposition_v1090 import load_propositions,compose_propositions
from subject_keyed_proposition_v1090 import load_subject_index,compose_subject_from_index
from typed_subject_proposition_v10100 import load_typed_index,compose_typed_rows
from rse_real_memory_readonly_v013588314 import jsonl

def duplicate(text):
    return bool(re.search(r"である(?:である)+(?=[。．.!！?？]|$)",str(text)))

def diagnose(subject,atomic_path,subject_path,typed_path,unified_path):
    atomic=[p for p in load_propositions(Path(atomic_path)) if p.subject==subject]
    indexed=[p for p in load_subject_index(Path(subject_path)) if p.subject==subject]
    typed=[p for p in load_typed_index(Path(typed_path)) if p.subject==subject]
    unified=[p for p in jsonl(unified_path) if str(p.get("concept","")).strip()==subject]
    atomic_compose=compose_propositions(atomic,subject=subject) if atomic else ""
    indexed_compose=compose_subject_from_index(Path(subject_path),subject) if indexed else ""
    typed_compose=compose_typed_rows(typed) if typed else ""
    stages={
        "atomic_values":[p.value for p in atomic],
        "atomic_compose":atomic_compose,
        "subject_index_values":[p.value for p in indexed],
        "subject_index_statements":[p.statement for p in indexed],
        "subject_index_compose":indexed_compose,
        "typed_values":[p.value for p in typed],
        "typed_statements":[p.statement for p in typed],
        "typed_compose":typed_compose,
        "unified_answers":[str(p.get("assistant","")) for p in unified]
    }
    flags={
        "atomic_values_with_copula":[i for i,x in enumerate(stages["atomic_values"]) if x.endswith("である")],
        "subject_values_with_copula":[i for i,x in enumerate(stages["subject_index_values"]) if x.endswith("である")],
        "typed_values_with_copula":[i for i,x in enumerate(stages["typed_values"]) if x.endswith("である")],
        "duplicated_at":[k for k,v in stages.items() if (any(duplicate(x) for x in v) if isinstance(v,list) else duplicate(v))]
    }
    return {"status":"READ_ONLY_COMPOSE_DIAGNOSTIC","subject":subject,
            "counts":{"atomic":len(atomic),"subject_index":len(indexed),"typed":len(typed),"unified":len(unified)},
            "stages":stages,"flags":flags,
            "possible_mechanism":"VALUE_ALREADY_HAS_COPULA" if flags["atomic_values_with_copula"] else "REQUIRES_SOURCE_INSPECTION",
            "stores_modified":False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--subject",default="閃亜鉛鉱")
    p.add_argument("--atomic",default="data/semantic_propositions_v1090.jsonl")
    p.add_argument("--subject-index",default="data/subject_keyed_propositions_v1090.jsonl")
    p.add_argument("--typed",default="data/typed_subject_propositions_v10100.jsonl")
    p.add_argument("--unified",default="data/unified_semantic_memory_v1090.jsonl")
    p.add_argument("--output",default="results/rse_proposition_compose_diagnostic_v013588316.json")
    a=p.parse_args()
    report=diagnose(a.subject,a.atomic,a.subject_index,a.typed,a.unified)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
