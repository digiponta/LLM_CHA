"""Read-only explanation of Nagato Semantic Memory counters.

The counters alone cannot prove checkpoint loss or successful internalization.
"""
import re

FIELDS=("corpus_records","subjects","unified_added","unified_preserved","internalized","pending")
def parse_memory_status(line):
    if not line.startswith("[Nagato Semantic Memory:"):
        return None
    values={k:int(m.group(1)) for k in FIELDS if (m:=re.search(r"\b"+k+r"=(\d+)",line))}
    if "internalized" not in values or "pending" not in values:
        return None
    if values["internalized"]==0 and values["pending"]>0:
        state="PENDING_REINTERNALIZATION_CHECK"
        note="56件などのpendingは再内部化待ちを示しますが、重み消失の証明ではありません。チェックポイント/メタデータ照合が必要です。"
    elif values["internalized"]>0 and values["pending"]==0:
        state="REPORTED_INTERNALIZED"
        note="内部化済み件数の表示です。重みの実測検証ではありません。"
    else:
        state="MIXED_OR_EMPTY"
        note="pending/internalizedの内訳をチェックしてください。"
    return {"status":state,"counters":values,"interpretation":note,"checkpoint_verified":False}
