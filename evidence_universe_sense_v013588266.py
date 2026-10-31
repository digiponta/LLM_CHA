"""Evidence-only disambiguated answer: prefer universe, otherwise outer space.

Never manufacture a meaning without a corresponding sentence in the source.
"""
import re
from question_aware_evidence_v013588255 import split_sentences
from evidence_conditioned_generation_v013588228 import evidence_gate

def resolve_universe(question,evidence):
    if not (question.strip() in ("宇宙とは","宇宙とは？","宇宙とは?","宇宙って何","宇宙とは何ですか") or
            question.strip() in ("宇宙空間とは","宇宙空間とは？","宇宙空間とは?")):
        return None
    sentences=split_sentences(evidence.get("excerpt",""))
    universe=None;space=None
    for s in sentences:
        if not 15<=len(s)<=300:continue
        if evidence_gate(s,evidence)[0]!="ACCEPT_SOURCE_EXTRACT":continue
        if re.search(r"(?:英語\s*universe|universe\s*は)",s,re.I) and "すべての物と事象の総体" in s:
            universe=s
        elif re.search(r"outer space|大気圏外の空間",s,re.I) and re.search(r"宇宙空間|外宇宙",s):
            space=s
    requested_space="宇宙空間" in question
    if requested_space and space:
        kind="OUTER_SPACE";selected=space
        value="宇宙空間（outer space）は、天体の大気圏外の空間を指します。"
        note="「宇宙全体（universe）」とは異なる語義です。"
    elif not requested_space and universe:
        kind="UNIVERSE";selected=universe
        value="宇宙（universe）は、すべての物と事象の総体を意味します。"
        note="「宇宙」は大気圏外の「宇宙空間（outer space）」を指す場合もあります。"
    elif not requested_space and space:
        # A partial source may describe outer space but not universe itself.
        kind="OUTER_SPACE_ONLY";selected=space
        value="この資料で確認できる「宇宙」は、大気圏外の宇宙空間（outer space）を指します。"
        note="宇宙全体（universe）の定義は、この抜粋からは確認できません。"
    else:return None
    return {"status":"BOUND_SENSE_NOTICE","sense":kind,"sentence":selected,
            "answer":value+"\n※語義の注意: "+note+"\n根拠: "+selected+
                     "\n出典: "+str(evidence.get("url",""))+"（外部未検証）"}
