"""v0.13.43: choose BPE prefix cut points only where decoded UTF-8 is intact.

Important: never replace a fixed length with silently corrupt decoded text.
Pick the nearest valid cut at or before the desired token position.
"""
def safe_prefix_ids(tokenizer, sentence, desired_tokens):
    if desired_tokens < 0:raise ValueError("negative prefix")
    ids=tokenizer.encode(sentence)
    if desired_tokens >= len(ids):return None
    for n in range(desired_tokens,-1,-1):
        left=tokenizer.decode(ids[:n])
        right=tokenizer.decode(ids[n:])
        if "\ufffd" in left or "\ufffd" in right:
            continue
        if left+right != tokenizer.decode(ids):
            continue
        return {"requested_tokens":desired_tokens,"actual_tokens":n,
                "prefix_ids":ids[:n],"suffix_ids":ids[n:],
                "prefix":left,"reference_continuation":right}
    return None
