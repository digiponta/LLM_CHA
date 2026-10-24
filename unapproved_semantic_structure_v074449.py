"""Conservative structure extraction for unapproved Wikipedia sentences."""
import re

def extract_structure(sentence, article_title):
    text=(sentence or "").strip().rstrip("。")
    # Prefer explicit article subject, not an inferred pronoun.
    subject=re.escape(article_title or "")
    if not subject:
        return {"status":"UNSTRUCTURED","reason":"NO_SUBJECT"}
    patterns=[
        (r"(?P<sub>"+subject+r")は(?P<obj>[^。]{2,90}?)をとることができる", "can_take_state"),
        (r"(?P<sub>"+subject+r")は(?P<obj>[^。]{2,90}?)である$", "is"),
        (r"(?P<sub>"+subject+r")は(?P<obj>[^。]{2,90}?)を表現する", "represents"),
    ]
    for pattern,relation in patterns:
        match=re.search(pattern,text)
        if not match:continue
        obj=match.group("obj").strip(" 、")
        if not obj or obj.startswith(("それ","その","これ","前述","上述")):
            continue
        return {"status":"STRUCTURED","subject":article_title,
                "relation":relation,"object":obj,"condition":None,
                "extraction_method":"EXPLICIT_SURFACE_PATTERN",
                "verified":False}
    return {"status":"UNSTRUCTURED","reason":"NO_EXPLICIT_PATTERN"}
