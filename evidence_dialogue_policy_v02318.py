"""v0.2.31.8: evidence-aware dialogue action and natural Japanese questions.

Frozen v0.2.31.5 parser and v0.2.31.7 baseline; no LM training.
Cues from original utterance are deliberately limited to explicit
surface evidence, not a claim of semantic generalization.
"""
from dataclasses import dataclass,asdict
import json,re
from structured_semantic_purpose_v02315 import extract
from semantic_dialogue_policy_v02317 import decide as old_decide

LABELS={"learning":"学習","development":"開発","troubleshooting":"問題解決","casual":"雑談"}
# A small, independently auditable evidence layer for *explicit* intentions,
# specifically where the upstream parser missed an inflection.
EXPLICIT={
 "development":r"組み上げたい|組み立てたい|製作したい|制作したい|作りたい|開発したい|実装したい",
 "troubleshooting":r"出力がおかしい|動作がおかしい|起動できない|不具合|エラー|バグ",
 "learning":r"学んでから|習得したい|覚えたい|勉強したい|学習したい",
 "casual":r"気軽に話そう|おしゃべり|雑談|話しませんか",
}
MULTI_LINK=r"してから|した後|それから|学んでから|勉強して.+(?:開発|作)|(?:学習|勉強).+も.+(?:開発|作)"

@dataclass
class EvidenceDecision:
    action:str
    reason:str
    question:str|None
    plan:list[str]|None
    purposes:list[str]
    evidence_source:str
    confidence_kind:str="uncalibrated_similarity_not_probability"

def explicit_evidence(text):
    found=[]
    for purpose,pat in EXPLICIT.items():
        for match in re.finditer(pat,text):
            found.append((match.start(),purpose,match.group()))
    found.sort()
    return found

def decide(text,structure=None):
    s=structure if structure is not None else extract(text)
    old=old_decide(s)
    raw_cues=explicit_evidence(text)
    explicit=list(dict.fromkeys(p for _,p,_ in raw_cues))
    parsed=list(dict.fromkeys(s.purposes))
    # Explicit cues alone are not enough to override negation / preference.
    if s.polarity!="POSITIVE" or s.relation=="PREFERENCE":
        purposes=parsed
    else:
        purposes=list(dict.fromkeys(parsed+explicit))
    ambiguous=s.status=="NEEDS_CONFIRMATION" and not explicit
    if ambiguous:
        candidate=s.evidence.get("vector_candidate")
        label=LABELS.get(candidate)
        question=(f"{s.topic}について、{label}をしたいということでしょうか？"
                  if s.topic and label else
                  f"{s.topic or 'そのこと'}について、どのようなことをしたいですか？")
        return EvidenceDecision("ASK_CONFIRMATION","ambiguous purpose",question,None,
                                purposes,"vector_candidate_unconfirmed")
    if not purposes:
        return EvidenceDecision("ASK_CLARIFICATION","missing explicit purpose",
            f"{s.topic or '今の話題'}について、学習・開発・問題解決・雑談のどれを希望しますか？",
            None,purposes,"missing")
    if len(purposes)>1:
        # Multiple purposes require a plan; ordering is preserved only
        # when actually expressed by the user.
        return EvidenceDecision("PLAN","multiple purposes",None,
            [f"{i+1}. {LABELS.get(p,p)}" for i,p in enumerate(purposes)],
            purposes,"parser_and_explicit")
    p=purposes[0]
    if p=="casual":
        return EvidenceDecision("RESPOND","casual purpose",f"{s.topic or '最近のこと'}について、どんな話をしましょうか？",
                                None,purposes,"explicit_or_parser")
    if s.status=="NEEDS_CONFIRMATION" and not raw_cues:
        return EvidenceDecision("ASK_CONFIRMATION","weak evidence",
                                f"{s.topic or 'そのこと'}について、もう少し目的を教えてください。",
                                None,purposes,"weak_vector")
    return EvidenceDecision("HANDOFF","explicit single purpose",None,None,
                            purposes,"explicit_or_parser")

def compare(text):
    s=extract(text)
    old=old_decide(s)
    new=decide(text,s)
    return {"text":text,"topic":s.topic,"parser_purposes":s.purposes,
            "parser_status":s.status,"old_action":old.action,
            "new_action":new.action,"decision":asdict(new)}

def main():
    print("LLM_CHA Evidence-Aware Dialogue Policy v0.2.31.8 (/quit)")
    while True:
        try:text=input("You> ").strip()
        except (EOFError,KeyboardInterrupt):break
        if text=="/quit":break
        print(json.dumps(compare(text),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
