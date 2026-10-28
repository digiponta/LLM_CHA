"""v0.13.58.45 opt-in, fail-closed single-subject semantic follow-up.

All eligible facts are reloaded for each user turn; no persistent cache.
Audit is opt-in, append-only and contains routing metadata, not raw questions.
"""
import json,os,re
from pathlib import Path
from semantic_chat_optin_v0135843 import load_sources,respond
from provenance_semantic_memory_v0135841 import SUBJECT
def explicit_subject(q):
    return "吾輩は猫である" if re.sub(r"[『』\s]","",SUBJECT) in re.sub(r"[『』\s]","",q) else None
def followup(q,subject):
    if subject!=SUBJECT:return None
    q=q.strip()
    if not re.match(r"^(その|この)(作者|著者|語り手|視点|テーマ|作品)",q):return None
    return f"『{SUBJECT}』の{q[2:]}"
def route(q,context=None,environ=None):
    env=os.environ if environ is None else environ
    if env.get("LLM_CHA_SEMANTIC_RUNTIME")!="1":return None
    keys=("LLM_CHA_SEMANTIC_PROPOSITIONS","LLM_CHA_SEMANTIC_TRUTH","LLM_CHA_SEMANTIC_MANIFEST")
    if not all(env.get(k) for k in keys):return None
    subject=explicit_subject(q)
    resolved=q if subject else followup(q,context)
    if resolved is None:return None
    try:
        data=load_sources(*(Path(env[k]) for k in keys))
        result=respond(resolved,data)
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,json.JSONDecodeError):
        return None
    if result.get("status")!="ANSWERED" or not result.get("facts"):return None
    if any(f.get("approval_state")!="ASSISTANT_REVIEWED_EXPERIMENTAL" for f in result["facts"]):return None
    return {"result":result,"subject":SUBJECT,"followup":subject is None}
def audit(event,environ=None):
    env=os.environ if environ is None else environ
    file=env.get("LLM_CHA_SEMANTIC_AUDIT")
    if not file:return
    path=Path(file)
    try:
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open("a",encoding="utf-8") as f:
            f.write(json.dumps(event,ensure_ascii=False)+"\n")
    except OSError:
        pass # Optional diagnostics must never change chat routing.
