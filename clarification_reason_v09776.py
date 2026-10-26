"""Bounded new-reason parser for an active clarification prompt only."""
import re

def parse_clarification(text):
    t=str(text or "").strip()
    m=re.fullmatch(
        r"(?:本当は|実は)?(?P<quality>色の変化|色合い|透明感|輝き|形|色)"
        r"(?:が|のところが)(?:好き|心地よい|いい)(?:なんだ|です|だ|よ)?[。！! ]*", t)
    return m.group("quality") if m else None
