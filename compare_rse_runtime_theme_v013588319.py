"""Read-only comparison: legacy Unified resolution vs proposed Theme RSE.

Do not claim to execute chat.py: its live route also includes typed, canonical,
truth-aware, topic context and other gates. This tool compares its documented
UNIFIED lookup component against Theme RSE on local stores.
"""
import argparse,json
from pathlib import Path
from knowledge_state_resolver_v10100 import extract_query_focus,unified_lookup_row
from rse_memory_state_compat_v013588315 import shadow
from rse_real_memory_readonly_v013588314 import jsonl

def compare(query,unified,truth,candidates):
    focus=extract_query_focus(query)
    row=unified_lookup_row(Path(unified),focus) if focus else None
    legacy={"route":"UNIFIED" if row else "NO_UNIFIED_HIT",
            "answer":str(row.get("assistant","")).strip() if row else None,
            "focus":focus,"provenance":str(row.get("source","")) if row else None,
            "note":"Legacy UNIFIED component only; not full chat.py execution"}
    new=shadow(query,unified,truth,candidates)
    if row:
        preservation="PRESERVED_IN_SHADOW_PREVIEW" if new.get("legacy_answer_preview")==legacy["answer"] else "MISMATCH"
    else:
        preservation="NOT_APPLICABLE"
    return {"status":"READ_ONLY_COMPONENT_COMPARISON","query":query,
            "legacy_unified":legacy,"rse_shadow":new,
            "legacy_answer_preservation":preservation,
            "chat_py_executed":False,"chat_py_modified":False,
            "live_rse_enabled":False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--query",action="append",required=True)
    p.add_argument("--unified",default="data/unified_semantic_memory_v1090.jsonl")
    p.add_argument("--truth",default="data/truth_state_v10103.jsonl")
    p.add_argument("--candidates",default="data/rse_theme_examples_v013588312.json")
    p.add_argument("--output",default="results/rse_runtime_theme_comparison_v013588319.json")
    a=p.parse_args()
    data=json.loads(Path(a.candidates).read_text(encoding="utf-8-sig"))
    reports=[compare(q,a.unified,a.truth,data["candidates"]) for q in a.query]
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps({"status":"READ_ONLY_COMPONENT_COMPARISON","cases":reports},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"READ_ONLY_COMPONENT_COMPARISON","cases":[
        {"query":x["query"],"legacy_route":x["legacy_unified"]["route"],
         "rse_status":x["rse_shadow"]["status"],
         "legacy_answer_preservation":x["legacy_answer_preservation"]}
         for x in reports]},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
