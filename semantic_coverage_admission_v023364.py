"""v0.2.33.64: read-only, conservative semantic coverage/admission diagnostic.

Distinguishes exact proposition coverage from concept-level presence and
dispatcher truth decisions. Never promotes a source to verified evidence.
"""
from pathlib import Path
from multilayer_semantic_audit_v023363 import audit_layers
from unified_semantic_bridge_v1090 import load_unified_rows
from structural_semantic_consistency_v023359 import clean
from evidence_grounded_reference_v023357 import evidence_gate
import json

def corpus_concept_hits(path,concept):
    p=Path(path)
    if not p.is_file():return 0
    n=0
    for number,line in enumerate(p.read_text(encoding="utf8").splitlines(),1):
        if not line.strip():continue
        try:obj=json.loads(line)
        except ValueError as exc:raise ValueError(f"invalid corpus row {number}") from exc
        if not isinstance(obj,dict):raise ValueError(f"invalid corpus row {number}")
        if clean(obj.get("subject",obj.get("concept","")))==clean(concept):
            n+=1
    return n

def inspect_coverage(concept,atomic_path,subject_path,typed_path,unified_path,
                     corpus_path,semantic,manifest_path=None):
    audit=audit_layers(atomic_path,subject_path,typed_path,unified_path,concept=concept)
    unified_count=sum(clean(r.get("concept",""))==clean(concept)
                      for r in load_unified_rows(Path(unified_path)))
    corpus_count=corpus_concept_hits(corpus_path,concept)
    result=semantic.resolve(f"{concept}とは")
    eligible,reason=evidence_gate(result)
    manifest_exists=bool(manifest_path and Path(manifest_path).is_file())
    return {"concept":concept,"atomic":audit["canonical_propositions"],
            "subject_index":sum("subject_index" in r["layers"] for r in audit["rows"]),
            "typed_index":sum("typed_index" in r["layers"] for r in audit["rows"]),
            "derived_orphans":audit["orphaned_derived"],
            "unified_concepts":unified_count,"corpus_records":corpus_count,
            "knowledge_state":str(getattr(result,"state","UNKNOWN")),
            "truth_state":str(getattr(result,"truth_state","UNVERIFIED") or "UNVERIFIED"),
            "evidence_admissible":eligible,"admission_reason":reason,
            "manifest_present":manifest_exists,
            "note":"Coverage and manifest presence do not prove factual correctness."}

def render_coverage(x):
    return (f"[Semantic Coverage: {x['concept']}] atomic={x['atomic']} "
            f"subject={x['subject_index']} typed={x['typed_index']} "
            f"unified={x['unified_concepts']} corpus={x['corpus_records']} "
            f"orphans={x['derived_orphans']} / Knowledge={x['knowledge_state']} "
            f"Truth={x['truth_state']} / Evidence="
            f"{'eligible_by_metadata' if x['evidence_admissible'] else 'BLOCK'}"
            f"({x['admission_reason']}) / manifest={'yes' if x['manifest_present'] else 'no'}")
