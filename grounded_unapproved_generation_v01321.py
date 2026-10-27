"""v0.13.21 strictly source-grounded generation guard.

Accept only a verbatim contiguous excerpt from the source. Otherwise fallback.
This is intentionally strict: fluency/paraphrase support is not yet proven.
"""
import re

def grounded_prompt(question, evidence):
    source=evidence["source_text"].strip()
    return ("人: 次の未承認・未検証の原文だけを根拠に、質問に関係する部分を原文どおり抜き出してください。"
            "原文に定義がなければ定義を作らないでください。\n"
            f"質問: {question}\n原文: {source}\nAI: ")

def validate_generation(candidate, evidence):
    source=re.sub(r"\s+","",evidence["source_text"])
    answer=re.sub(r"\s+","",candidate.strip())
    answer=answer.strip("「」『』")
    if not answer or len(answer)<8:
        return False,"EMPTY_OR_TOO_SHORT"
    if len(answer)>len(source):
        return False,"LONGER_THAN_SOURCE"
    if answer not in source:
        return False,"NOT_VERBATIM_SOURCE_EXCERPT"
    return True,"VERBATIM_SOURCE_EXCERPT"

def choose_answer(candidate,evidence):
    ok,reason=validate_generation(candidate,evidence)
    if ok:
        return {"answer":"【未承認・事実未検証／原文抜粋】"+candidate.strip(),
                "route":"GROUNDED_EXCERPT","validation":reason}
    from trained_unapproved_binding_v01320 import format_quotation
    return {"answer":format_quotation(evidence),
            "route":"SOURCE_QUOTATION_FALLBACK","validation":reason}
