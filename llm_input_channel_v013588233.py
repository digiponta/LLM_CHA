"""Validate CLI stdin before registration; return categorized send failures."""
import re

def normalize_one_line(prompt):
    if not isinstance(prompt,str):
        raise TypeError("PROMPT_NOT_TEXT")
    return re.sub(r"\\s+", " ", prompt).strip()

def send_one_line(proc,prompt):
    prompt=normalize_one_line(prompt)
    if not prompt:
        raise ValueError("PROMPT_EMPTY")
    if proc is None or proc.poll() is not None:
        raise RuntimeError("PROCESS_NOT_RUNNING")
    stream=getattr(proc,"stdin",None)
    if stream is None or stream.closed or not stream.writable():
        raise ValueError("STDIN_UNAVAILABLE")
    stream.write((prompt+"\n").encode("utf-8"))
    stream.flush()
