"""v0.2.33.59: restricted structural semantic consistency validator.

Conservative grammar only. NOT a general Japanese semantic entailment engine.
Supports XはY (positive/negative), XはYを含む, and 条件CではXはY.
Any unsupported grammar blocks, including directional inversion and omitted conditions.
"""
import re,unicodedata
from evidence_grounded_reference_v023357 import evidence_gate

def clean(s):
    s=unicodedata.normalize("NFKC",str(s or "")).strip()
    return s.rstrip("。.!?！？ ").strip()

def parse(s):
    s=clean(s)
    condition=""
    m=re.fullmatch(r"条件(.+?)では(.+)",s)
    if m: condition,s=m.group(1).strip(),m.group(2).strip()
    m=re.fullmatch(r"(.+?)は(.+?)を含(む|まない)",s)
    if m:
        return ("includes",clean(m[1]),clean(m[2]),m[3]=="む",condition)
    m=re.fullmatch(r"(.+?)は(.+?)に適(する|さない)",s)
    if m:
        return ("suitable_for",clean(m[1]),clean(m[2]),m[3]=="する",condition)
    m=re.fullmatch(r"(.+?)は(.+?)で(ある|はない)",s)
    if m:
        return ("is_a",clean(m[1]),clean(m[2]),m[3]=="ある",condition)
    return None

def structural_support(result):
    evidence=str(getattr(getattr(result,"provenance",None),"evidence","") or "")
    answer=str(getattr(result,"answer","") or "")
    e=parse(evidence);a=parse(answer)
    if e is None or a is None:return False,"unsupported_grammar"
    if e[4]!=a[4]:return False,"condition_mismatch"
    if e[0]!=a[0]:return False,"relation_mismatch"
    if e[1]!=a[1] or e[2]!=a[2]:return False,"argument_mismatch"
    if e[3]!=a[3]:return False,"polarity_mismatch"
    return True,"exact_structural_match"

class StructuralReferenceBridge:
    def __init__(self,references,mappings,semantic):
        self.references=references;self.mappings=mappings;self.semantic=semantic
    def lookup(self,context):
        reference=self.references.lookup(context,"experiment","target")
        if reference is None:return {"status":"no_approved_reference"}
        mapping=self.mappings.lookup(context,reference)
        if mapping is None:return {"status":"no_approved_mapping","reference":reference}
        result=self.semantic.resolve(f"{mapping['concept']}とは")
        accepted,reason=evidence_gate(result)
        if accepted:accepted,reason=structural_support(result)
        p=getattr(result,"provenance",None)
        return {"status":"structural_match" if accepted else "structural_blocked",
                "reason":reason,"reference":reference,"concept":mapping["concept"],
                "truth_state":str(result.truth_state or "UNVERIFIED"),
                "source":str(getattr(p,"source","") or ""),
                "answer":str(result.answer) if accepted else ""}

def render_structural(r):
    if r["status"]=="no_approved_reference":return "承認済み参照がありません。"
    if r["status"]=="no_approved_mapping":return "承認済み概念対応がありません。"
    head=f"[参照 {r['reference']} → {r['concept']}; Truth={r['truth_state']}; source={r['source']}]"
    return head+(" 構造一致の回答候補: "+r["answer"] if r["status"]=="structural_match"
                 else " 回答保留（"+r["reason"]+"）。")
