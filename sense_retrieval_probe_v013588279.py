"""Read-only three-question Semantic Memory retrieval smoke test.

Uses registered atomic propositions and the AI-delegated provenance record.
Does not infer a chemical formula or modify model weights, chat.py or stores.
"""
import argparse,json
from pathlib import Path
from semantic_proposition_v1090 import load_propositions
from unified_semantic_bridge_v1090 import load_unified_rows

QUESTIONS=("閃亜鉛鉱とは？","スファレライトとは？","閃亜鉛鉱の化学組成は？")
TARGET="閃亜鉛鉱"
ALIAS="スファレライト"

def probe(atomic,unified,audit,questions=QUESTIONS):
    propositions=load_propositions(Path(atomic))
    unified_rows=load_unified_rows(Path(unified))
    provenance=json.loads(Path(audit).read_text(encoding="utf-8-sig"))
    if not isinstance(provenance,list):raise ValueError("INVALID_AUDIT")
    entries=[x for x in provenance if x.get("subject")==TARGET and x.get("candidate_id")=="sense-ab912703fcc269a1"]
    facts=[p for p in propositions if p.subject==TARGET]
    stored=[x for x in unified_rows if x.get("concept")==TARGET]
    if len(entries)!=1 or not facts or not stored:
        status="SOURCE_NOT_READY"
    else:status="READY"
    source=entries[0] if len(entries)==1 else {}
    alias_supported=ALIAS in source.get("evidence_sentence","")
    answers=[]
    for question in questions:
        q=str(question).strip()
        if status!="READY":
            route="SOURCE_NOT_READY";answer="登録された知識の整合性を確認できません。"
        elif q in ("閃亜鉛鉱とは？","閃亜鉛鉱とは","閃亜鉛鉱"):
            route="ATOMIC_EXACT";answer="閃亜鉛鉱は、"+facts[0].value.rstrip("。")+"。"
        elif q in ("スファレライトとは？","スファレライトとは","スファレライト") and alias_supported:
            route="EVIDENCE_ALIAS";answer="スファレライトは閃亜鉛鉱の別名です。"+ "閃亜鉛鉱は、"+facts[0].value.rstrip("。")+"。"
        elif "化学組成" in q and TARGET in q:
            route="ATTRIBUTE_NOT_EXPLICIT";answer="登録済み命題には化学式が明示されていません。資料の追加確認が必要です。"
        else:
            route="UNKNOWN";answer="未学習です。"
        answers.append({"question":q,"route":route,"answer":answer})
    return {"status":"RETRIEVAL_SMOKE_DIAGNOSTIC","source_status":status,
            "atomic_matches":len(facts),"unified_matches":len(stored),
            "provenance_matches":len(entries),"alias_supported":alias_supported,
            "answers":answers,"production_changed":False,"model_changed":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--atomic",default="data/semantic_propositions_v1090.jsonl")
    p.add_argument("--unified",default="data/unified_semantic_memory_v1090.jsonl")
    p.add_argument("--provenance",default="data/sense_registration_provenance_v013588273.json")
    p.add_argument("--output",default="results/sense_retrieval_probe_v013588279.json")
    a=p.parse_args()
    result=probe(a.atomic,a.unified,a.provenance)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
