"""v0.7.44.30: exact Wikipedia wikitext <math> evidence, no invented equation."""
import re
from wikipedia_acquisition_v0517 import _request

MATH = re.compile(r"<math(?:\s+[^>]*)?>(.*?)</math>", re.S | re.I)
PROSE = re.compile(r"[ぁ-んァ-ヶ一-龯]")
BLOCKED = ("\\write", "\\input", "\\include", "\\href", "\\html", "\\require", "\\newcommand")

def complete_formula(latex):
    """Conservative display gate: reject leading operators and unmatched groups."""
    if not isinstance(latex, str) or not latex.strip() or len(latex) > 300:
        return False
    t=latex.strip()
    if t[0] in "=+*/^_)}]" or t[-1] in "=+*/^_({[":
        return False
    if any(token in t.lower() for token in BLOCKED):
        return False
    for left,right in (("{","}"),("(",")"),("[","]")):
        if t.count(left) != t.count(right):
            return False
    if t.count(r"\left") != t.count(r"\right"):
        return False
    return bool(re.search(r"[=\\^_]",t) or len(t)>18)

def equation_rank(latex):
    """Prefer complete relations; suppress isolated symbols and state labels."""
    t=latex.strip()
    if "=" in t:
        return 100 + min(len(t),100)
    if r"\rangle" in t and ("+" in t or "-" in t):
        return 80 + min(len(t),100)
    return -1

def math_blocks(wiki, fetch=None, limit=12):
    if not isinstance(wiki, dict) or wiki.get("status") != "FOUND":
        return []
    title, url = wiki.get("title"), wiki.get("url")
    if not isinstance(title, str) or not title or not isinstance(url, str) or not url.startswith("https://ja.wikipedia.org/wiki/"):
        return []
    try:
        data = _request({"action":"query","prop":"revisions","titles":title,
                         "rvslots":"main","rvprop":"content","format":"json",
                         "formatversion":2}, fetch)
        pages = data.get("query", {}).get("pages", [])
        if len(pages)!=1 or pages[0].get("missing") or pages[0].get("title")!=title:
            return []
        revs=pages[0].get("revisions", [])
        raw=revs[0].get("slots",{}).get("main",{}).get("content","") if revs else ""
        if not isinstance(raw,str) or not raw:
            return []
        blocks=[]
        for match in MATH.finditer(raw):
            latex=match.group(1).strip()
            if not complete_formula(latex) or equation_rank(latex) < 0:
                continue
            # Only a source-identical TeX span is displayed; no interpolation.
            if not (re.search(r"[=\\^_]",latex) or len(latex)>18):
                continue
            prefix=raw[max(0,match.start()-180):match.start()]
            # Avoid fabricating polished prose from wikitext templates.
            plain=re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]",r"\1",prefix)
            plain=re.sub(r"<!--.*?-->|<[^>]*>|\{\{.*?\}\}", " ", plain, flags=re.S)
            plain=plain.split("。")[-1].split("\n")[-1].strip(" =:;*#")
            description=plain if 8<=len(plain)<=120 and len(PROSE.findall(plain))>=8 and not any(c in plain for c in "{}[]|") and not re.search(r"\\s{2,}",plain) and not plain.startswith(("ここで", "は", "が", "これを")) and not plain.endswith(("、", "：", ":", "は", "を", "が", "では")) else ""
            blocks.append({"title":title,"source":url,"latex":latex,
                           "description":description,"truth_state":"EXTERNAL_UNVERIFIED",
                           "train_ready":False,"auto_promote":False})
        blocks.sort(key=lambda b: -equation_rank(b["latex"]))
        return blocks[:limit]
    except (OSError,ValueError,TypeError,KeyError,TimeoutError):
        return []

class EquationCursor:
    def __init__(self):
        self.identity=None
        self.used=set()
    def reset(self):
        self.identity=None
        self.used.clear()
    def next(self,wiki,fetch=None):
        if not isinstance(wiki,dict):
            return None
        identity=(wiki.get("title"),wiki.get("url"))
        if identity!=self.identity:
            self.identity=identity
            self.used.clear()
        unseen=[b for b in math_blocks(wiki,fetch=fetch) if b["latex"] not in self.used]
        if not unseen:
            return None
        # v0.7.44.35: connected equation evidence is shown together,
        # instead of treating each source equation as a separate chat turn.
        chosen=unseen[:2] if wiki.get("title")=="量子ビット" else unseen[:1]
        self.used.update(b["latex"] for b in chosen)
        answer="Wikipedia記事中の数式（外部資料・未検証）："
        for block in chosen:
            label=block["description"] or "数式"
            answer+="\n"+label+"： LATEX( "+block["latex"]+" ) [数式原文: "+block["latex"]+"]"
        return {"title":wiki.get("title"),"source":wiki.get("url"),
                "latex":chosen[0]["latex"],"description":chosen[0]["description"],
                "answer":answer,"blocks":chosen,
                "truth_state":"EXTERNAL_UNVERIFIED","train_ready":False,
                "auto_promote":False,"route":"WIKIPEDIA_EQUATION_EVIDENCE",
                "quality_gate":"SOURCE_WIKITEXT_MATH_EXACT"}
