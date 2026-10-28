"""v0.13.58.44: conservative opt-in chat semantic response router.

Default OFF; experimental fixture source is never silently enabled.
No online training, promotion, or persistence. On abstain return None so
chat.py continues through its unchanged legacy path.
"""
import os
from pathlib import Path
from semantic_chat_optin_v0135843 import load_sources,respond

def route(question, *, environ=None):
    env=os.environ if environ is None else environ
    if env.get("LLM_CHA_SEMANTIC_RUNTIME")!="1":return None
    if not all(env.get(k) for k in ("LLM_CHA_SEMANTIC_PROPOSITIONS","LLM_CHA_SEMANTIC_TRUTH","LLM_CHA_SEMANTIC_MANIFEST")):
        return None
    try:
        source=load_sources(Path(env["LLM_CHA_SEMANTIC_PROPOSITIONS"]),
            Path(env["LLM_CHA_SEMANTIC_TRUTH"]),Path(env["LLM_CHA_SEMANTIC_MANIFEST"]))
        outcome=respond(question,source)
    except (OSError,ValueError,KeyError,TypeError):
        return None
    if outcome["status"]!="ANSWERED" or not outcome.get("facts"):return None
    if any(f.get("approval_state")!="ASSISTANT_REVIEWED_EXPERIMENTAL" for f in outcome["facts"]):
        return None
    return outcome
