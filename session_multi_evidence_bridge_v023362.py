"""v0.2.33.62: opt-in, read-only bridge to multiple atomic propositions.

Atomic proposition presence alone never establishes TRUE. Each chain edge needs
an exact statement in the real proposition store AND a separately curated
evidence manifest entry. Nothing writes semantic memory or model weights.
"""
import json
from pathlib import Path
from semantic_proposition_v1090 import load_propositions
from multi_proposition_evidence_v023361 import Evidence,validate
from structural_semantic_consistency_v023359 import parse,clean

class MultiEvidenceBridge:
    def __init__(self,references,mappings,proposition_path,manifest_path):
        self.references=references
        self.mappings=mappings
        self.proposition_path=Path(proposition_path)
        self.manifest_path=Path(manifest_path)
    def lookup(self,context,candidate):
        reference=self.references.lookup(context,"experiment","target")
        if reference is None:return {"status":"blocked","reason":"no_approved_reference","path":[]}
        mapping=self.mappings.lookup(context,reference)
        if mapping is None:return {"status":"blocked","reason":"no_approved_mapping","path":[]}
        target=parse(candidate)
        if target is None or target[0]!="includes" or not target[3]:
            return {"status":"blocked","reason":"unsupported_candidate","path":[]}
        # Explicitly tie the requested proof's subject to the mapped concept.
        if target[1]!=mapping["concept"]:
            return {"status":"blocked","reason":"mapped_subject_mismatch","path":[]}
        if not self.manifest_path.is_file():
            return {"status":"blocked","reason":"no_evidence_manifest","path":[]}
        manifest=json.loads(self.manifest_path.read_text(encoding="utf8"))
        if manifest.get("schema")!=1 or manifest.get("transitive_relations")!=["includes"]:
            return {"status":"blocked","reason":"invalid_policy_manifest","path":[]}
        entries=manifest.get("evidence")
        if not isinstance(entries,list):
            return {"status":"blocked","reason":"invalid_evidence_manifest","path":[]}
        # Atomic proposition values can preserve a typed relation phrase.
        # Match precisely against the stored subject + relation value, without
        # assigning TRUE to unrelated raw statements.
        stored={clean(f"{p.subject}は{p.value}") for p in load_propositions(self.proposition_path)}
        evidence=[];seen_ids=set()
        for entry in entries:
            if not isinstance(entry,dict):
                return {"status":"blocked","reason":"invalid_evidence_entry","path":[]}
            statement=clean(entry.get("statement",""))
            eid=str(entry.get("evidence_id",""))
            if not eid or eid in seen_ids:
                return {"status":"blocked","reason":"duplicate_or_missing_evidence_id","path":[]}
            seen_ids.add(eid)
            if statement not in stored:
                return {"status":"blocked","reason":"manifest_statement_not_in_semantic_memory","path":[]}
            if entry.get("truth")!="TRUE" or not entry.get("source"):
                return {"status":"blocked","reason":"unvalidated_manifest_entry","path":[]}
            if parse(statement) is None:
                return {"status":"blocked","reason":"unsupported_manifest_statement","path":[]}
            evidence.append(Evidence(statement,"TRUE",str(entry["source"]),eid))
        result=validate(evidence,candidate,transitive_relations=frozenset({"includes"}))
        return {**result,"reference":reference,"concept":mapping["concept"],
                "source":"atomic_proposition_exact_match+explicit_manifest",
                "caveat":"Manifest approval is a local claim; external truth not independently verified."}

def render_multi_evidence(result):
    if result["status"]=="supported":
        return ("[証拠連鎖候補 / 外部検証未実施] "+
                " → ".join(result["path"])+" / "+result["reason"])
    return "[回答保留] "+result["reason"]
