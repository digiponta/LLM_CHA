"""v0.7.32: status-only parser for LLM_CHA GUI mirror.
Never turns diagnostics into conversation text or verified claims.
"""
import re

def parse_status(line):
    text=line.strip()
    if text.startswith("[Nagato Semantic Memory:"):
        m=re.search(r"\binternalized=(\d+)",text)
        p=re.search(r"\bpending=(\d+)",text)
        if m:
            return {"trusted":f"Trusted: {m.group(1)} internalized",
                    "trusted_pending":f"Trusted pending: {p.group(1)}" if p else None}
    if text.startswith("[experimental startup restore:"):
        m=re.search(r"\bstatus=([A-Z_]+)",text)
        count=re.search(r"\bcandidate_count=(\d+)",text)
        result={"experimental":f"Experimental: {m.group(1)}" if m else "Experimental: unknown"}
        if count:result["candidate"]=f"Candidates: {count.group(1)} PENDING"
        return result
    if text.startswith("[experimental sleep:"):
        status=re.search(r"\bstatus=([A-Z_]+)",text)
        pending=re.search(r"\bpending=(\d+)",text)
        return {"experimental":"Experimental sleep: "+(status.group(1) if status else "unknown"),
                "candidate":f"Candidates: {pending.group(1)} PENDING" if pending else None}
    if text.startswith("[experimental adapter reload:"):
        status=re.search(r"\bstatus=([A-Z_]+)",text)
        return {"experimental":"Adapter: "+(status.group(1) if status else "unknown")}
    if text.startswith("[retrieval-first="):
        route=re.search(r"\broute=([A-Z_]+)",text)
        return {"route":f"Last route: {route.group(1)}" if route else "Last route: Trusted retrieval"}
    if text.startswith("[route="):
        route=re.search(r"\broute=([A-Z_]+)",text)
        truth=re.search(r"\btruth_state=([A-Z_]+)",text)
        value=route.group(1) if route else "UNKNOWN"
        return {"route":"Last route: "+value+(" (unverified)" if truth and "UNVERIFIED" in truth.group(1) else "")}
    if text.startswith("[experimental_route="):
        return {"route":"Last route: EXPERIMENTAL_UNKNOWN"}
    if text.startswith("[route=RAW_CONCEPT_EVIDENCE"):
        return {"route":"Last route: RAW_CONCEPT_EVIDENCE (unverified)"}
    return {}

class StatusParser:
    def __init__(self, emit):
        self.emit=emit
        self.buffer=""
    def feed(self, char):
        self.buffer+=char
        while "\n" in self.buffer:
            line,self.buffer=self.buffer.split("\n",1)
            update=parse_status(line)
            if update:self.emit(update)
