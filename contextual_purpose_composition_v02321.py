"""v0.2.32.1 contextual reference resolution + incremental purpose composition.

A conservative stateful adapter over frozen v0.2.31.9 DSS. Does not
claim neural coreference resolution or actual generation.
"""
from dataclasses import asdict
import re,json
from evidence_dialogue_state_v02319 import DialogueState,step as legacy_step,utterance_response
from evidence_dialogue_policy_v02318 import decide
from structured_semantic_purpose_v02315 import extract
from purpose_confidence_v02311 import topic_of

REFERENT=re.compile(r"それ|その件|その話|これ|それについて")
ADDITION=re.compile(r"それから|その後|(?:さらに|加えて)|(?:も|もまた)したい")
SEQUENCE=re.compile(r"それから|その後|してから|した後")
EXPLICIT_SWITCH=re.compile(r"やっぱり|それより|代わりに|変更したい|話題を変え")
# Limited paraphrases targeting observable referent and purpose phenomena.
PURPOSE_PHRASES=(
 ("development",r"作ってみたい|作りたい|開発したい|実装したい|自作したい"),
 ("learning",r"勉強したい|学習したい|学びたい"),
 ("troubleshooting",r"直したい|修正したい"),
 ("casual",r"雑談したい|話したい"),
)
def resolve(d,text):
    """Return a trace; carry topic only when there is a grounded prior topic."""
    topic=topic_of(text)
    anaphora=bool(REFERENT.search(text))
    return {"topic":topic or (d.topic if anaphora else None),
            "used_prior_topic":bool(anaphora and not topic and d.topic),
            "anaphora":anaphora}

def purpose_evidence(text):
    matches=[]
    for purpose,pattern in PURPOSE_PHRASES:
        for m in re.finditer(pattern,text):
            matches.append((m.start(),purpose))
    return list(dict.fromkeys(p for _,p in sorted(matches)))

def step(d,text):
    raw=text.strip()
    reference=resolve(d,raw)
    addition=bool(ADDITION.search(raw))
    switched=bool(EXPLICIT_SWITCH.search(raw))
    fresh_topic=topic_of(raw)
    goals=purpose_evidence(raw)
    # Only intercept demonstrably state-dependent turns, leaving the
    # baseline's confirmation/negation and ordinary parsing untouched.
    can_add=(addition and not switched and not fresh_topic and d.topic
             and d.purposes and goals)
    can_replace=(reference["used_prior_topic"] and goals and not addition and not switched)
    if not (can_add or can_replace):
        return legacy_step(d,text)
    d.turns+=1
    if can_add:
        d.purposes=list(dict.fromkeys(d.purposes+goals))
        if SEQUENCE.search(raw):d.relation="SEQUENTIAL"
        action="PLAN" if len(d.purposes)>1 else "HANDOFF"
    else:
        d.purposes=list(goals)
        d.relation="UNSPECIFIED"
        action="RESPOND" if goals==["casual"] else ("PLAN" if len(goals)>1 else "HANDOFF")
    d.pending_purpose=None
    d.pending_question=None
    d.rejected=[]
    reply=utterance_response(d,action)
    d.history.append({"user":raw,"action":action,"response":reply,
                      "topic":d.topic,"purposes":list(d.purposes),"state":d.state,
                      "resolution":reference,"update":"ADD" if can_add else "REPLACE"})
    return d,action,reply

def generation_context(d,action,raw):
    """Explicit, serializable boundary for a later generator adapter."""
    return {"user_input":raw,"topic":d.topic,"purposes":list(d.purposes),
            "relation":d.relation,"action":action,
            "history":list(d.history),"requires_generation":action in ("HANDOFF","RESPOND","PLAN")}

def main():
    d=DialogueState()
    print("LLM_CHA Contextual Purpose Composition v0.2.32.1")
    print("Commands: /state /reset /quit")
    while True:
        try:raw=input("You> ")
        except (EOFError,KeyboardInterrupt):break
        if raw.strip()=="/quit":break
        if raw.strip()=="/reset":d=DialogueState();print("DSS reset");continue
        if raw.strip()=="/state":
            print(json.dumps(asdict(d),ensure_ascii=False,indent=2));continue
        d,action,answer=step(d,raw)
        print(f"CHA[{d.state}/{action}]> {answer}")
if __name__=="__main__":main()
