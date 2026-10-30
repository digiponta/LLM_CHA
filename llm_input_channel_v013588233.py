"""Validate CLI stdin before registration; return categorized send failures."""
def send_one_line(proc,prompt):
    if not isinstance(prompt,str) or "\n" in prompt or "\r" in prompt:
        raise ValueError("PROMPT_MULTILINE")
    if proc is None or proc.poll() is not None:
        raise RuntimeError("PROCESS_NOT_RUNNING")
    stream=getattr(proc,"stdin",None)
    if stream is None or stream.closed or not stream.writable():
        raise ValueError("STDIN_UNAVAILABLE")
    stream.write((prompt+"\n").encode("utf-8"))
    stream.flush()
