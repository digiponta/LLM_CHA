"""v0.7.10 — trusted-first, unknown-triggered experimental fallback.

The unapproved model is consulted ONLY when the trusted route explicitly
returns UNKNOWN. Its answer remains EXTERNAL_UNVERIFIED/EXPERIMENTAL and may
never be promoted or used as approved knowledge implicitly.
"""
from dataclasses import dataclass
from typing import Callable, Any

UNKNOWN="UNKNOWN"
ANSWER="ANSWER"

@dataclass(frozen=True)
class RouteResult:
    status: str
    text: str = ""
    source: str = ""
    provenance: str = ""

def normalize(value: Any) -> RouteResult:
    if isinstance(value, RouteResult):
        result=value
    elif isinstance(value,dict):
        result=RouteResult(**value)
    else:
        raise TypeError("route result must be RouteResult or dict")
    if result.status not in (UNKNOWN,ANSWER):
        raise ValueError("invalid route status")
    if result.status==ANSWER and not result.text.strip():
        raise ValueError("empty answer must not be marked ANSWER")
    return result

def trusted_first(question: str,
                  approved_ask: Callable[[str],RouteResult],
                  experimental_ask: Callable[[str],RouteResult],
                  *,allow_experimental: bool=False) -> dict:
    if not isinstance(question,str) or not question.strip():
        raise ValueError("question required")
    primary=normalize(approved_ask(question))
    if primary.status==ANSWER:
        return {"route":"TRUSTED","answer":primary.text,
                "truth_state":"APPROVED","source":primary.source,
                "provenance":primary.provenance,
                "consulted_experimental":False,"auto_promote":False}
    if not allow_experimental:
        return {"route":"TRUSTED_UNKNOWN","answer":"承認済み知識では回答できません。",
                "truth_state":"UNKNOWN","source":primary.source,
                "provenance":primary.provenance,
                "consulted_experimental":False,"auto_promote":False}
    secondary=normalize(experimental_ask(question))
    if secondary.status==UNKNOWN:
        return {"route":"EXPERIMENTAL_UNKNOWN","answer":"承認済み・未承認のいずれも回答できません。",
                "truth_state":"UNKNOWN","source":secondary.source,
                "provenance":secondary.provenance,
                "consulted_experimental":True,"auto_promote":False}
    return {"route":"EXPERIMENTAL_FALLBACK",
            "answer":"【未承認・実験的回答】"+secondary.text,
            "truth_state":"EXPERIMENTAL_UNVERIFIED",
            "source":secondary.source,"provenance":secondary.provenance,
            "consulted_experimental":True,"auto_promote":False}
