"""Explicit, read-only source-grounded chat diagnostic for CLI and GUI.

Uses saved v0.60 Wikipedia snapshots only; no network, model training or writes.
An exact evidence extract is NOT independent confirmation of accuracy.
"""
import json,re
from pathlib import Path
from evidence_dynamic_definition_v013588263 import answer_or_abstain
from evidence_alias_normalization_v013588261 import matches_subject
from evidence_universe_sense_v013588266 import resolve_universe
from evidence_generalized_sense_v013588267 import resolve as resolve_generalized_sense

DEFAULT_SNAPSHOT=Path(__file__).resolve().parent/"data/wiki_evidence_review_v013588260.json"
ABSTAIN="提示された資料では、質問の対象・関係・回答値を確認できません。"

def _unsafe_universe_sense(question,result):
    if "宇宙" not in question or "宇宙空間" in question:return False
    if result.get("status")!="BOUND_EXTRACT_ACCEPTED":return False
    sentence=result.get("sentence") or ""
    return bool(re.search(r"outer space|大気圏外|外宇宙|宇宙空間",sentence,re.I) and
                not re.search(r"すべての物と事象の総体|時間、空間内|時空.*全体",sentence))

def answer(question,snapshot_path=DEFAULT_SNAPSHOT):
    q=str(question or "").strip()
    if not q:return {"status":"ABSTAIN_EMPTY_QUESTION","answer":ABSTAIN}
    path=Path(snapshot_path)
    if not path.is_file():
        return {"status":"ABSTAIN_NO_SNAPSHOT","answer":"Evidenceスナップショットがありません。先に収集してください。"}
    try:
        data=json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError,ValueError) as exc:
        return {"status":"ABSTAIN_SNAPSHOT_ERROR","answer":"Evidenceファイルを読み込めません: "+type(exc).__name__}
    matches=[item for item in data.get("cases",[]) if
             matches_subject(q,item.get("source",{}).get("title",""),item.get("evidence",{}).get("excerpt",""))]
    if len(matches)!=1:
        return {"status":"ABSTAIN_NO_UNIQUE_SOURCE" if not matches else "ABSTAIN_AMBIGUOUS_SOURCE",
                "answer":"質問に一致する一意の資料を選べません。対象名を指定してください。"}
    item=matches[0]
    evidence=dict(item["evidence"])
    evidence["topic"]=item["source"]["title"]
    result=resolve_universe(q,evidence)
    if result is None:
        result=resolve_generalized_sense(q,evidence)
    if result is None:
        result=answer_or_abstain(q,evidence)
    if _unsafe_universe_sense(q,result):
        result={"status":"ABSTAIN_SENSE_MISMATCH","answer":
                "宇宙全体と宇宙空間の語義が混在しているため、根拠の採用を保留します。"}
    review=item.get("review",{})
    if result["status"] in ("BOUND_EXTRACT_ACCEPTED","BOUND_SENSE_NOTICE"):
        text=result["answer"]+"\n［資料は外部未検証・人手レビュー未承認。回答の正確性は保証されません］"
    else:
        text=result.get("answer",ABSTAIN)
    return {"status":result["status"],"answer":text,"source_id":item.get("id"),
            "source_url":evidence.get("url"),"review_status":review.get("status","UNKNOWN"),
            "source_trust":"EXTERNAL_UNVERIFIED","production_changed":False}
