"""Conservative acceptance guard for visibly malformed low-agreement generations.

It does not reject merely because lexical agreement is low. Only clear
surface corruption combined with low probe agreement blocks acceptance.
"""
import re

def assess(answer,agreement,threshold,accepted=True):
    if not accepted:return {"accepted":False,"reason":"PREVIOUS_GATE_REJECT"}
    t=str(answer or "").strip()
    if not t:return {"accepted":False,"reason":"EMPTY_GENERATION"}
    if agreement>=threshold:return {"accepted":True,"reason":"AGREEMENT_NOT_LOW"}
    # A reply starting with sentence-terminal punctuation is a clear failure,
    # not merely a stylistic issue.
    if re.match(r"^[。．.!！?？、，,;；]",t):
        return {"accepted":False,"reason":"MALFORMED_LEADING_PUNCTUATION_LOW_AGREEMENT"}
    return {"accepted":True,"reason":"NO_CLEAR_SURFACE_DEFECT"}
