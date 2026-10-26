"""Normalize supported Japanese causal questions without changing evidence."""
import re

def normalize_causal_question(question):
    q = str(question or "").strip()
    if not q or q.startswith("/"):
        return q
    q = q.rstrip(" 　。？！?!")
    # Normalize polite and colloquial requests to the existing intent patterns.
    q = q.replace("どうして", "なぜ")
    q = re.sub(r"(?:のでしょうか|んですか|のですか|んだろう|なの|の)$", "", q)
    if re.search(r"(?:カット|加工)", q) and re.search(r"(?:困難|難しい|難しく|難しさ)", q):
        return "なぜカットが難しい" if re.search(r"(?:なぜ|理由|原因|どうして)", q) else q
    if re.search(r"(?:虹色|ファイア|輝)", q) and re.search(r"(?:なぜ|理由|原因)", q):
        return "なぜ虹色に輝く"
    return q
