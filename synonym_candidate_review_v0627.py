"""v0.6.27: extract synonym *candidates* from text; never auto-promote.

Rules are deliberately conservative. Co-occurrence, relatedness, and hyponymy
are not equivalence. Proposal records remain pending until explicit approval.
"""
import json
import re
from pathlib import Path
from synonym_lexicon_v0626 import clean_term

TERM=r"[一-龯ぁ-んァ-ヶーA-Za-z0-9]{1,40}"
PATTERNS=[
    re.compile(rf"[「『]?({TERM})[」』]?は[、，, ]*[「『]?({TERM})[」』]?の(?:別名|同義語|異表記)(?:です|だ|である)?"),
    re.compile(rf"[「『]?({TERM})[」』]?も[「『]?({TERM})[」』]?の(?:別名|同義語|異表記)(?:です|だ|である)?"),
    re.compile(rf"[「『]?({TERM})[」』]?と[「『]?({TERM})[」』]?は(?:同義語|同じ意味|異表記)"),
]
def extract_candidates(text):
    result=[]
    for pattern in PATTERNS:
        for match in pattern.finditer(text):
            a,b=map(clean_term,match.groups())
            if a!=b and (a,b) not in result and (b,a) not in result:
                result.append((a,b))
    return result

class SynonymReview:
    def __init__(self,path,lexicon):
        self.path=Path(path)
        self.lexicon=lexicon
        self.records=[]
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():self.records.append(json.loads(line))
    def _save(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.path.write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in self.records),encoding="utf-8")
    def propose(self,text):
        added=[]
        for a,b in extract_candidates(text):
            if b in self.lexicon.expand(a):continue
            key=frozenset((a,b))
            if any(frozenset((r["a"],r["b"]))==key for r in self.records):
                continue
            record={"id":max((r["id"] for r in self.records),default=0)+1,
                    "a":a,"b":b,"state":"PENDING","source_text":text[:500],
                    "source":"TEXT_PATTERN","confidence":None}
            self.records.append(record)
            added.append(record)
        if added:self._save()
        return added
    def pending(self):
        return [r for r in self.records if r["state"]=="PENDING"]
    def decide(self,record_id,approve):
        r=next((row for row in self.records if row["id"]==record_id),None)
        if r is None or r["state"]!="PENDING":return None
        if approve:self.lexicon.add(r["a"],r["b"])
        r["state"]="APPROVED" if approve else "REJECTED"
        self._save()
        return r
