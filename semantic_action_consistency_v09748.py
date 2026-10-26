"""v0.9.7.48 bounded subject/action/object consistency checks.

Evidence-preserving, narrow Japanese past-tense patterns only.
Unknown or ambiguous structures do not trigger automatic corrections.
"""
from dataclasses import dataclass,asdict
import re

ACTIONS={"食べた":"EAT","飲んだ":"DRINK","買った":"BUY","借りた":"BORROW","見た":"SEE","聞いた":"HEAR","行った":"GO",
         "食べなかった":"EAT","飲まなかった":"DRINK","買わなかった":"BUY","借りなかった":"BORROW",
         "見なかった":"SEE","聞かなかった":"HEAR","行かなかった":"GO"}
NEGATIVE=frozenset(x for x in ACTIONS if "なかった" in x)
VERBS="|".join(map(re.escape,sorted(ACTIONS,key=len,reverse=True)))
PATTERN=re.compile(r"(?P<object>[^。！？\n]{1,100}?)(?P<particle>を|に|へ)(?P<verb>"+VERBS+r")")
CONTRADICTIONS={"EAT":{"DRINK"},"DRINK":{"EAT"},"BUY":{"BORROW"},"BORROW":{"BUY"},"SEE":{"HEAR"},"HEAR":{"SEE"}}

@dataclass(frozen=True)
class ActionFact:
    subject:str
    action:str
    object:str
    negated:bool
    verb:str
    source:str
    train_ready:bool=False
    auto_promote:bool=False
    def snapshot(self):return asdict(self)

@dataclass(frozen=True)
class ActionCheck:
    decision:str
    reason:str
    original:str
    selected:str
    input_fact:dict|None
    output_fact:dict|None
    train_ready:bool=False
    auto_promote:bool=False
    persisted:bool=False
    def snapshot(self):return asdict(self)

def extract(text,source):
    s=str(text or "").strip()
    if source=="ASSISTANT_RESPONSE":
        s=re.sub(r"^(?:そう[、，]|うん[、，])\s*", "", s)
    hits=list(PATTERN.finditer(s))
    if len(hits)!=1:return None
    m=hits[0]
    obj=m.group("object").strip(" 、，　")
    # Conservative: do not infer a referent from quoted, compounded
    # or explicitly multiple-clause statements.
    if not obj or any(c in obj for c in "「」『』？?、。！!\n"):
        return None
    verb=m.group("verb")
    return ActionFact("USER",ACTIONS[verb],obj,verb in NEGATIVE,verb,source)

def check(utterance,response):
    original=str(response or "")
    user=extract(utterance,"USER_UTTERANCE")
    ai=extract(response,"ASSISTANT_RESPONSE")
    if user is None or ai is None:
        return ActionCheck("REVIEW","unsupported-or-ambiguous-syntax",original,original,
                           user.snapshot() if user else None,ai.snapshot() if ai else None)
    # Allow the answer to include an acknowledgment before the object's name.
    left=user.object
    right=ai.object
    if left!=right:
        return ActionCheck("REVIEW","object-identity-not-established",original,original,
                           user.snapshot(),ai.snapshot())
    if user.action==ai.action and user.negated==ai.negated:
        return ActionCheck("CONSISTENT","action-and-polarity-match",original,original,user.snapshot(),ai.snapshot())
    mismatch=(user.action==ai.action or ai.action in CONTRADICTIONS.get(user.action,set()))
    if not mismatch:
        return ActionCheck("REVIEW","unrelated-actions",original,original,user.snapshot(),ai.snapshot())
    # Replace only the exact verb following an identical object. Preserve
    # grammatical particle; do not assume へ/に movement equivalents.
    found=list(PATTERN.finditer(original))
    if len(found)!=1:
        return ActionCheck("REVIEW","uncertain-output-span",original,original,user.snapshot(),ai.snapshot())
    match=found[0]
    if match.group("particle")!=("を" if user.action!="GO" else "へ"):
        # avoid replacing differing grammatical roles.
        if user.action!="GO" or match.group("particle") not in ("へ","に"):
            return ActionCheck("REVIEW","particle-mismatch",original,original,user.snapshot(),ai.snapshot())
    revised=original[:match.start("verb")]+user.verb+original[match.end("verb"):]
    return ActionCheck("REPAIR","explicit-user-action-priority",original,revised,user.snapshot(),ai.snapshot())
