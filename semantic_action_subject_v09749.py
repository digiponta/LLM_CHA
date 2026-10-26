"""Conservative v0.9.7.49 subject-aware Semantic Action Gate.

Only single-clause, unquoted, unambiguous past-tense user reports.
Uncertain coreference must never trigger an automatic repair.
"""
from dataclasses import dataclass,asdict
import re
from semantic_action_consistency_v09748 import ACTIONS,NEGATIVE,CONTRADICTIONS,ActionCheck

VERBS="|".join(re.escape(v) for v in sorted(ACTIONS,key=len,reverse=True))
PAT=re.compile(r"^(?:(?P<subject>私は|私が|僕は|僕が|友人は|友人が|彼は|彼が|彼女は|彼女が|母は|母が)\s*)?(?P<object>[^「」『』。！？?!、\n]{1,90}?)(?P<particle>を|に|へ)(?P<verb>"+VERBS+r")(?P<tail>のね|んだね|んですね|ね|よ|。|！|!|？|\?|だったね|)?[。！!？?]*$")
SUBJECTS={"私は":"SPEAKER","私が":"SPEAKER","僕は":"SPEAKER","僕が":"SPEAKER",
          "友人は":"FRIEND","友人が":"FRIEND","彼は":"HE","彼が":"HE",
          "彼女は":"SHE","彼女が":"SHE","母は":"MOTHER","母が":"MOTHER"}

@dataclass(frozen=True)
class SemanticAction:
    subject:str
    subject_explicit:bool
    action:str
    object:str
    negated:bool
    verb:str
    source:str
    def snapshot(self):return asdict(self)

def parse(text,source):
    s=str(text or "").strip()
    if source=="ASSISTANT_RESPONSE":
        s=re.sub(r"^(?:そう[、，]|うん[、，])\s*","",s)
    if "けれど" in s or "けど" in s or "\n" in s:return None
    m=PAT.fullmatch(s)
    if m is None:return None
    obj=m.group("object").strip()
    if not obj or any(x in obj for x in ("そして","それから","、","私は","友人は","彼は","彼女は")):return None
    verb=m.group("verb")
    subject=m.group("subject")
    return SemanticAction(SUBJECTS.get(subject,"UNSPECIFIED"),bool(subject),
                          ACTIONS[verb],obj,verb in NEGATIVE,verb,source)

def check(utterance,response):
    original=str(response or "")
    u=parse(utterance,"USER_UTTERANCE")
    a=parse(response,"ASSISTANT_RESPONSE")
    base=lambda decision,reason,selected: ActionCheck(
        decision,reason,original,selected,
        u.snapshot() if u else None,a.snapshot() if a else None)
    if u is None or a is None:return base("REVIEW","ambiguous-or-multi-clause",original)
    if u.object!=a.object:return base("REVIEW","different-object",original)
    if a.subject_explicit and u.subject_explicit and a.subject!=u.subject:
        return base("REVIEW","subject-mismatch",original)
    if u.subject_explicit and not a.subject_explicit:
        # Response subject is implicit: coreference cannot be proven.
        return base("REVIEW","unresolved-response-subject",original)
    if not u.subject_explicit and a.subject_explicit:
        return base("REVIEW","unresolved-user-subject",original)
    if u.action==a.action and u.negated==a.negated:
        return base("CONSISTENT","subject-action-object-polarity-match",original)
    if a.action!=u.action and a.action not in CONTRADICTIONS.get(u.action,set()):
        return base("REVIEW","unrelated-actions",original)
    # Replace only an unambiguous exact verb span in the already parsed reply.
    prefix=re.match(r"^(?:そう[、，]|うん[、，])\s*",original)
    offset=prefix.end() if prefix else 0
    m=PAT.fullmatch(original[offset:].strip())
    if m is None or m.group("particle")!=("を" if u.action!="GO" else m.group("particle")):
        return base("REVIEW","particle-or-span-uncertain",original)
    start=offset+m.start("verb");end=offset+m.end("verb")
    return base("REPAIR","subject-action-consistency",original[:start]+u.verb+original[end:])
