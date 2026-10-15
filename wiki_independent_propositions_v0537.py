"""v0.5.37 independent Japanese atomic clauses; limited explicit patterns only."""
import re
from wiki_typed_propositions_v0532 import _record

PATTERNS=(
 (r"^(.+?)は(.+?)を含む$", "contains","COMPONENT"),
 (r"^(.+?)は(.+?)を検出する$", "detects","FUNCTION"),
 (r"^(.+?)は(.+?)に基づく$", "based_on","STRUCTURE"),
 (r"^(.+?)は(.+?)に基く$", "based_on","STRUCTURE"),
)
def extract_independent(sentence,source=None):
    if not isinstance(sentence,str):return []
    raw=sentence.strip()
    core=raw.rstrip("。").strip()
    for pattern,predicate,kind in PATTERNS:
        match=re.fullmatch(pattern,core)
        if not match:continue
        subject,obj=(x.strip() for x in match.groups())
        if not subject or not obj or any(x in subject+obj for x in ("。","\n","、")):continue
        part={"source":source,"original":raw,"text":raw}
        return [_record(subject,predicate,obj,kind,core,part)]
    return []
