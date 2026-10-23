"""Extract a readable Wikipedia lead without splitting at periods inside parentheses."""
import re

def wiki_lead(extract,max_chars=240):
    if not isinstance(extract,str):return None
    text=re.sub(r"\s+"," ",extract).strip()
    if not text:return None
    depth=0
    for i,ch in enumerate(text):
        if ch in "（(":depth+=1
        elif ch in "）)":depth=max(0,depth-1)
        elif ch=="。" and depth==0:
            candidate=text[:i+1].strip()
            if len(candidate)>=18 and not candidate.endswith(("とは、。","は、。","とは。")):
                return candidate[:max_chars].rstrip("、")+"…" if len(candidate)>max_chars else candidate
    if len(text)>max_chars:return text[:max_chars].rstrip("、。 ")+"…"
    if text.endswith(("とは、","は、","とは","は")):return None
    return text if text.endswith("。") else text+"。"
