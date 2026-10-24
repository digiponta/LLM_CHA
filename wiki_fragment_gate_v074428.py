"""v0.7.44.28 reject contextless mathematical fragments from Wiki extracts."""
import re
from wiki_math_integrity_v074421 import safe_evidence_sentence

def coherent_scientific_evidence(text):
    if not isinstance(text,str) or not safe_evidence_sentence(text):
        return False
    s=text.strip()
    if len(s)<25: return False
    # A TeX/glyph-only orphan is not a scientific explanation.
    if re.fullmatch(r"[{}\\$\s\w^_+*/=(),.\[\]−∞ħψΨ]+",s):
        return False
    if s.startswith(("は", "が", "を", "に", "では", "ならびに")):
        return False
    # Truncated equations and deictic clauses require a prior equation.
    if re.search(r"(以下のように表される|次式で表される|次の式で表される)$",s):
        return False
    if re.search(r"\{\\displaystyle",s) and s.count("{") != s.count("}"):
        return False
    if s.startswith(("名前は", "名称は")):
        return False
    return len(re.findall(r"[ぁ-んァ-ヶ一-龯]",s))>=12
