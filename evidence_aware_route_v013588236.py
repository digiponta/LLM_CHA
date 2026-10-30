"""Explicit one-line evidence candidate transport for the local CLI.

This only requests a *candidate*. It never approves or learns an answer.
"""
import base64
import json
import re

PREFIX="/evidence-candidate "

def encode_request(topic,excerpt):
    data={"topic":str(topic)[:100],"excerpt":str(excerpt)[:450]}
    wire=json.dumps(data,ensure_ascii=False,separators=(",",":")).encode("utf-8")
    return PREFIX+base64.urlsafe_b64encode(wire).decode("ascii")

def decode_request(line):
    if not line.startswith(PREFIX):
        raise ValueError("NOT_EVIDENCE_COMMAND")
    token=line[len(PREFIX):].strip()
    if not token or len(token)>4096 or not re.fullmatch(r"[A-Za-z0-9_=-]+",token):
        raise ValueError("INVALID_EVIDENCE_TOKEN")
    try:
        payload=json.loads(base64.b64decode(token,altchars=b"-_",validate=True))
    except (ValueError,UnicodeDecodeError) as exc:
        raise ValueError("INVALID_EVIDENCE_PAYLOAD") from exc
    if not isinstance(payload,dict) or not isinstance(payload.get("topic"),str) or not isinstance(payload.get("excerpt"),str):
        raise ValueError("INVALID_EVIDENCE_FIELDS")
    topic=re.sub(r"\s+"," ",payload["topic"]).strip()[:100]
    excerpt=re.sub(r"\s+"," ",payload["excerpt"]).strip()[:450]
    if not topic or not excerpt:
        raise ValueError("EMPTY_EVIDENCE_FIELDS")
    return topic,excerpt

def generation_prompt(topic,excerpt):
    # Prompt text is explicitly untrusted. Output still requires the GUI evidence gate.
    return ("人: "+topic+"を説明してください。参考文: "+excerpt+"\nAI:")
