"""v0.4.14: conservative classification of definition vs property vs attribution.

Diagnostic only; v0.4.12 extractor and Truth Gate are unchanged.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from article_proposition_alignment_v0412 import align as align_v0412
from external_candidate_store_v0407 import _atomic_write

DEFINITION="DEFINITION_CANDIDATE"
PROPERTY="PROPERTY"
ATTRIBUTED="ATTRIBUTED_CLAIM"
CONTEXT="CONTEXT_DEPENDENT"
UNRESOLVED="UNRESOLVED"

def classify(evidence):
    base=align_v0412(evidence)  # validates schema and source digest
    text=evidence["lead_extract"]
    topic=evidence["concept"].strip()
    items=[]
    for segment in re.finditer(r"[^。！？\n]+(?:[。！？]|$)",text):
        raw=segment.group().strip()
        if not raw:continue
        start=segment.start()+len(segment.group())-len(segment.group().lstrip())
        end=start+len(raw)
        if text[start:end]!=raw:raise ValueError("source span mismatch")
        # This deliberately examines all sentences, including those not extracted by v0.4.12.
        if any(marker in raw for marker in ("とされる","と言われる","と考えられる","という説","と呼ばれる")):
            cls,why=ATTRIBUTED,"explicit_attribution_marker"
        elif any(marker in raw for marker in ("しかし","ただし","一方","という仮説","と仮定","仮に","もし","ではない","わけではない")) or raw.endswith(("？","！")):
            cls,why=CONTEXT,"context_or_scope_guard"
        elif raw.startswith(topic) and (raw.endswith(("広大である。","高速である。","重要である。","便利である。")) or "ことができる" in raw):
            cls,why=PROPERTY,"descriptive_property_marker"
        elif "を" in raw and raw.endswith("という。"):
            cls,why=DEFINITION,"naming_definition_pattern"
        elif any(p["evidence_start"]==start and p["evidence_end"]==end for p in base["propositions"]):
            cls,why=DEFINITION,"v0412_extract_with_no_additional_boundary"
        else:
            cls,why=UNRESOLVED,"insufficient_definition_evidence"
        items.append({"classification":cls,"reason":why,"literal":raw,
                      "evidence_start":start,"evidence_end":end,
                      "factual_truth":"UNVERIFIED","eligible_for_training":False,
                      "review_state":"PENDING_REVIEW"})
    return {"version":"v0.4.14","concept":topic,"source_version":"v0.4.9",
            "baseline_extracted":base["proposition_count"],
            "items":items,"truth_promotions":0,"semantic_memory_writes":0,
            "training_enabled":False,"classification_is_truth":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--evidence",required=True)
    p.add_argument("--report")
    args=p.parse_args()
    try:
        path=Path(args.evidence)
        if path.stat().st_size>128_000:raise ValueError("evidence file too large")
        out=classify(json.loads(path.read_text(encoding="utf-8")))
        if args.report:
            if Path(args.report).resolve()==path.resolve():raise ValueError("refusing input overwrite")
            _atomic_write(args.report,out)
        print(json.dumps(out,ensure_ascii=False,indent=2))
    except (ValueError,OSError,TypeError,KeyError,json.JSONDecodeError) as e:
        p.exit(1,f"v0.4.14 failed: {type(e).__name__}: {e}\n")
if __name__=="__main__":main()
