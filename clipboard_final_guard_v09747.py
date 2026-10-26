"""Clipboard final-answer guard: respect user's explicit eat/drink action.

Conservative exact overlap only; never changes source verification status.
"""
import re
from final_answer_guard_v09746 import inspect_answer,FinalDecision
from semantic_action_consistency_v09748 import check as action_check
from semantic_action_subject_v09749 import check as subject_check

FOOD_WORDS=("バゲットサンド","サンドイッチ","ケーキ","パイ","スコーン")
DRINK_WORDS=("ラテ","コーヒー","フラペチーノ","ジュース","紅茶")
EAT_PATTERN=re.compile(r"(?P<item>[\w&®・ 　]+(?:バゲットサンド|サンドイッチ|ケーキ|パイ|スコーン))を(?P<verb>食べた|飲んだ)")
DRINK_PATTERN=re.compile(r"(?P<item>[\w&®・ 　]+(?:ラテ|コーヒー|フラペチーノ|ジュース|紅茶))を(?P<verb>飲んだ|食べた)")

def inspect_clipboard_answer(user_text,answer):
    user=str(user_text or "").strip()
    output=str(answer or "").strip()
    subject=subject_check(user,output)
    if subject.decision=="REPAIR":
        return FinalDecision("REJECT","subject-action-consistency",output,
                             subject.selected,"CLIPBOARD_CONTEXT_ANSWER")
    if subject.reason in ("subject-mismatch","unresolved-response-subject","unresolved-user-subject"):
        return FinalDecision("REVIEW",subject.reason,output,output,"CLIPBOARD_CONTEXT_ANSWER")
    action=action_check(user,output)
    if action.decision=="REPAIR":
        return FinalDecision("REJECT","semantic-action-consistency",output,
                             action.selected,"CLIPBOARD_CONTEXT_ANSWER")
    for pattern,preferred in ((EAT_PATTERN,"食べた"),(DRINK_PATTERN,"飲んだ")):
        match=pattern.search(user)
        if match is None or match.group("verb")!=preferred:
            continue
        item=match.group("item").strip()
        # Only substitute if the answer refers to the same mentioned item;
        # do not alter other statements or third-party quotations.
        if item not in output:
            continue
        opposite="飲んだ" if preferred=="食べた" else "食べた"
        wrong=item+"を"+opposite
        if wrong in output:
            revised=output.replace(wrong,item+"を"+preferred,1)
            return FinalDecision("REJECT","explicit-user-action-conflict",output,
                                 revised,"CLIPBOARD_CONTEXT_ANSWER")
    return inspect_answer(user,output,"CLIPBOARD_CONTEXT_ANSWER")
