"""Conservative structure extraction for unapproved Wikipedia sentences."""
import re

EXTRACTOR_VERSION = "v0.7.44.52"

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
    # Conservative comparison: require both subjects in the source sentence.
    if article_title in text and "古典的なビット" in text and "重ね合わせ状態" in text:
        if re.search(r"古典的なビットが[^。]{2,100}?(?:のに対し|に対して)[^。]*"+subject+r"は[^。]*重ね合わせ状態",text):
            return {"status":"STRUCTURED","subject":article_title,
                    "relation":"can_have_superposition","object":"重ね合わせ状態",
                    "comparison_subject":"古典的なビット","condition":None,
                    "extraction_method":"EXPLICIT_COMPARISON_PATTERN","verified":False}
    if article_title in text and "基本単位" in text:
        if re.search(subject+r"[^。]{0,90}?(?:基本単位である|基本単位となる)$",text):
            return {"status":"STRUCTURED","subject":article_title,
                    "relation":"is_basic_unit","object":"基本単位",
                    "condition":None,"extraction_method":"EXPLICIT_BASIC_UNIT_PATTERN",
                    "verified":False}
    reason="DEICTIC_REFERENCE" if text.startswith(("それ","その","これ","前述","上述")) else "NO_EXPLICIT_PATTERN"
    return {"status":"UNSTRUCTURED","reason":reason}
