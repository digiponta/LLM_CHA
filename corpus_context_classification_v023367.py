"""v0.2.33.67: source-anchored mention and epistemic *heuristic* extraction.

All mention occurrences are retained (including multiple occurrences per line).
Markers describe the *writing style*, NOT whether the assertion is true.
No changes to Semantic Memory, Truth State or model weights.
"""
import hashlib,json,re,sqlite3,time
from contextlib import contextmanager
from pathlib import Path
from structural_semantic_consistency_v023359 import clean,parse

@contextmanager
def connection(path):
    db=sqlite3.connect(str(path),timeout=10)
    try:
        with db:yield db
    finally:db.close()

def classify(sentence):
    hints=[]
    for label,pattern in (
        ("HYPOTHESIS",r"かもしれない|可能性|だろう|多分|もし|としたら|不明|気になる"),
        ("ANALOGY",r"ようなもの|ように|アナロジ|例える|たとえ|類似|みたい"),
        ("OPINION",r"思う|考えると|見方|観点|感じる|ではないか"),
    ):
        if re.search(pattern,sentence):hints.append(label)
    if not hints:
        hints=["STRUCTURAL_CANDIDATE"] if parse(clean(sentence)) else ["CONTEXT_ONLY"]
    return hints

def mentions(path,concept,limit=1000):
    if not concept:raise ValueError("empty_concept")
    if not 1<=limit<=10000:raise ValueError("invalid_limit")
    p=Path(path).resolve()
    data=p.read_bytes()
    text=data.decode("utf-8")
    file_digest=hashlib.sha256(data).hexdigest()
    rows=[]
    offsets=[0]
    for char in text:offsets.append(offsets[-1]+len(char.encode("utf-8")))
    for match in re.finditer(re.escape(concept),text):
        # Sentence context, split on Japanese full stop/newline; retain source offsets.
        start=max(text.rfind("。",0,match.start()),text.rfind("\n",0,match.start()))+1
        boundaries=[i for i in (text.find("。",match.end()),text.find("\n",match.end())) if i!=-1]
        end=min(boundaries)+1 if boundaries else len(text)
        sentence=text[start:end].strip()
        b0,b1=offsets[match.start()],offsets[match.end()]
        c0,c1=offsets[start],offsets[end]
        snippet=data[c0:c1]
        rows.append({"concept":concept,"mention_start":b0,"mention_end":b1,
                     "context_start":c0,"context_end":c1,
                     "context":sentence,"labels":classify(sentence),
                     "file_sha256":file_digest,
                     "context_sha256":hashlib.sha256(snippet).hexdigest(),
                     "source_path":str(p)})
        if len(rows)>=limit:break
    return rows

class MentionStore:
    def __init__(self,path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with connection(self.path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS mentions(
                token TEXT PRIMARY KEY,context TEXT NOT NULL,concept TEXT NOT NULL,
                source_path TEXT NOT NULL,file_sha256 TEXT NOT NULL,
                mention_start INTEGER NOT NULL,mention_end INTEGER NOT NULL,
                context_start INTEGER NOT NULL,context_end INTEGER NOT NULL,
                context_sha256 TEXT NOT NULL,sentence TEXT NOT NULL,
                labels_json TEXT NOT NULL,status TEXT NOT NULL,created REAL NOT NULL)""")
    def scan(self,context,concept,path):
        rows=mentions(path,concept)
        tokens=[]
        with connection(self.path) as db:
            for r in rows:
                digest=hashlib.sha256(("\0".join(str(v) for v in
                    (context,concept,r["source_path"],r["file_sha256"],
                     r["mention_start"],r["mention_end"]))).encode("utf-8")).hexdigest()
                token="mention-"+digest[:20]
                db.execute("""INSERT OR IGNORE INTO mentions VALUES
                    (?,?,?,?,?,?,?,?,?,?,?,?,'PENDING',?)""",
                    (token,context,concept,r["source_path"],r["file_sha256"],
                     r["mention_start"],r["mention_end"],r["context_start"],
                     r["context_end"],r["context_sha256"],r["context"],
                     json.dumps(r["labels"],ensure_ascii=False),time.time()))
                tokens.append(token)
        return tokens
    def list(self,context,concept):
        with connection(self.path) as db:
            rows=db.execute("""SELECT token,mention_start,sentence,labels_json,status,
                    file_sha256 FROM mentions WHERE context=? AND concept=?
                    ORDER BY mention_start,token""",(context,concept)).fetchall()
        return [{"token":a,"byte":b,"sentence":c,"labels":json.loads(d),
                 "status":e,"file_sha256":f} for a,b,c,d,e,f in rows]

def render_mentions(rows):
    if not rows:return "[Concept Mention] 0件"
    return "\n".join(f"{r['token']} [{','.join(r['labels'])}] "
                     f"byte={r['byte']} {r['sentence']}" for r in rows)
