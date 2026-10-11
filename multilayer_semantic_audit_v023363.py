"""v0.2.33.63 read-only audit of atomic, subject, typed and unified layers.

Atomic propositions are canonical. Derived indexes count as corroborating
representations only, never independent evidence or TRUE assertions.
"""
from pathlib import Path
from semantic_proposition_v1090 import load_propositions
from subject_keyed_proposition_v1090 import load_subject_index
from typed_subject_proposition_v10100 import load_typed_index
from unified_semantic_bridge_v1090 import load_unified_rows
from structural_semantic_consistency_v023359 import clean

def audit_layers(atomic_path,subject_path,typed_path,unified_path,concept=None):
    atom={(clean(p.subject),clean(p.value)) for p in load_propositions(Path(atomic_path))}
    subject={(clean(p.subject),clean(p.value)) for p in load_subject_index(Path(subject_path))}
    typed={(clean(p.subject),clean(p.value)) for p in load_typed_index(Path(typed_path))}
    unified=load_unified_rows(Path(unified_path))
    names={clean(row.get("concept","")) for row in unified}
    selected=sorted(x for x in atom|subject|typed if concept is None or x[0]==clean(concept))
    rows=[]
    for s,v in selected:
        layers=([layer for layer,exists in
                (("atomic",(s,v) in atom),("subject_index",(s,v) in subject),
                 ("typed_index",(s,v) in typed)) if exists])
        rows.append({"statement":f"{s}は{v}","subject":s,"value":v,
                     "layers":layers,"canonical":(s,v) in atom,
                     "derived_orphan":(s,v) not in atom,
                     "unified_concept_present":s in names})
    return {"status":"audited","concept":concept,"unique_propositions":len(rows),
            "canonical_propositions":sum(x["canonical"] for x in rows),
            "orphaned_derived":sum(x["derived_orphan"] for x in rows),
            "rows":rows,"unified_concepts_matched":len({r["subject"] for r in rows if r["unified_concept_present"]}),
            "independent_evidence_count":0,
            "note":"Derived indexes/unified concepts are not independent evidence; truth remains UNVERIFIED unless separately curated."}

def render_audit(result):
    return ("[多層Semantic Memory監査] unique="+str(result["unique_propositions"])+
            " canonical="+str(result["canonical_propositions"])+
            " derived_orphans="+str(result["orphaned_derived"])+
            " unified_concepts="+str(result["unified_concepts_matched"])+
            " / 独立した検証済み証拠は自動認定しません。")
