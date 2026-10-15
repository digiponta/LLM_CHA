"""v0.5.63: conservative source-preserving scientific sentence parser."""
import re

MATH_OPEN = r"{\displaystyle"

def _math_end(text, start):
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    return None

def scientific_sentences(text):
    """Split on Japanese sentence stops, not line breaks inside math/prose."""
    if not isinstance(text, str):
        return []
    pieces = []
    start = 0
    i = 0
    while i < len(text):
        if text.startswith(MATH_OPEN, i):
            end = _math_end(text, i)
            if end is None:
                # Malformed source: fail closed on the rest of this segment.
                i = len(text)
                break
            i = end
            continue
        if text[i] == "。":
            part = text[start:i].strip()
            if part:
                pieces.append(part)
            start = i + 1
        i += 1
    if start < len(text):
        part = text[start:].strip()
        if part:
            pieces.append(part)
    return pieces

def scientific_prose(sentence):
    """Accept substantial prose with balanced TeX while excluding bare equations."""
    if not isinstance(sentence, str) or not 20 <= len(sentence) <= 1000:
        return False
    prose = []
    i = 0
    while i < len(sentence):
        if sentence.startswith(MATH_OPEN, i):
            end = _math_end(sentence, i)
            if end is None:
                return False
            i = end
            continue
        if sentence[i] in r"{}\\" or sentence[i] in "<>":
            return False
        prose.append(sentence[i])
        i += 1
    words = "".join(prose).strip()
    if len(re.findall(r"[ぁ-んァ-ヶ一-龯]", words)) < 12:
        return False
    return bool(re.search(
        r"(である|です|ます|れる|する|した|となる|できる|される|"
        r"と呼ぶ|と呼ばれる|記述される|表せない|表現できる|"
        r"という|がある|であり|ついてくる|となっている)$", words))
