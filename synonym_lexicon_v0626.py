"""v0.6.26 — persistent reviewed synonym lexicon and bounded query expansion.

Synonym links are lexical retrieval hints, NOT model-weight fine-tuning and NOT
proof that arbitrary propositions are true. Training is explicit via /synonym-add.
"""
import json
import re
from pathlib import Path

DEFAULT_PAIRS=(("猫","ネコ"),("猫","ねこ"))

def clean_term(term):
    term=str(term).strip()
    if not (1 <= len(term) <= 40) or any(c in term for c in "\r\n/\\=><"):
        raise ValueError("invalid synonym term")
    return term

class SynonymLexicon:
    def __init__(self, path):
        self.path=Path(path)
        self.edges={}
        self._add_initial()
        self.load()

    def _add_initial(self):
        for left,right in DEFAULT_PAIRS:
            self.add(left,right,save=False)

    def load(self):
        if not self.path.exists():
            return
        for line in self.path.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip():continue
            row=json.loads(line)
            if row.get("type")!="synonym_pair":continue
            self.add(row["a"],row["b"],save=False)

    def add(self,a,b,save=True):
        a,b=clean_term(a),clean_term(b)
        if a==b:raise ValueError("self synonym is not useful")
        already=b in self.edges.get(a,set())
        self.edges.setdefault(a,set()).add(b)
        self.edges.setdefault(b,set()).add(a)
        if save and not already:
            self.path.parent.mkdir(parents=True,exist_ok=True)
            with self.path.open("a",encoding="utf-8") as f:
                f.write(json.dumps({"type":"synonym_pair","a":a,"b":b,
                   "source":"USER_APPROVED","truth_state":"LEXICAL_EQUIVALENCE"},
                   ensure_ascii=False)+"\n")
        return not already

    def expand(self,term,limit=8):
        term=clean_term(term)
        seen={term}
        queue=[term]
        while queue and len(seen)<limit:
            current=queue.pop(0)
            for other in sorted(self.edges.get(current,())):
                if other not in seen:
                    seen.add(other)
                    queue.append(other)
                    if len(seen)>=limit:break
        return [term]+sorted(seen-{term})

def learn_command(text,lexicon):
    m=re.fullmatch(r"/synonym-add\s+([^\s=]+)\s*(?:=|＝|\s)\s*([^\s=]+)\s*",text)
    if not m:
        return None
    a,b=m.groups()
    changed=lexicon.add(a,b)
    return {"added":changed,"terms":lexicon.expand(a)}

def best_raw_mentions(path, terms, max_results=3):
    from raw_concept_evidence_v0615 import find_mentions
    hits=[]
    used=set()
    for term in terms:
        for row in find_mentions(path,term,max_results=max_results):
            key=(row["line"],row["text"])
            if key not in used:
                used.add(key)
                row=dict(row)
                row["matched_alias"]=term
                hits.append(row)
                if len(hits)>=max_results:return hits
    return hits

def learn_natural_statement(text, lexicon):
    """Parse explicit Japanese alias assertions; do not infer from similarity."""
    term=r"[一-龯ぁ-んァ-ヶーA-Za-z0-9]{1,40}"
    patterns=[
        rf"^[「『]?({term})[」』]?も[「『]?({term})[」』]?の(?:別名|同義語|言い換え)(?:です|だ|である)?[。！!]?\s*$",
        rf"^[「『]?({term})[」』]?は[「『]?({term})[」』]?の(?:別名|同義語)(?:です|だ|である)?[。！!]?\s*$",
        rf"^[「『]?({term})[」』]?と[「『]?({term})[」』]?は(?:同義語|同じ意味)(?:です|だ|である)?[。！!]?\s*$",
    ]
    for i,pattern in enumerate(patterns):
        m=re.fullmatch(pattern,text.strip())
        if m:
            left,right=m.groups()
            if i in (0,1):
                left,right=right,left
            changed=lexicon.add(left,right)
            return {"added":changed,"terms":lexicon.expand(left),
                    "source":"USER_STATEMENT"}
    return None
