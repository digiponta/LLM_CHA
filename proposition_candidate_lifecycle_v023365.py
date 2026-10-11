"""v0.2.33.65: reviewed proposition candidate lifecycle, isolated SQLite.

No writes to Semantic Memory, Truth State, model weights, or /sleep. Approval
records a human decision only; it is NOT a declaration of objective truth.
"""
import hashlib,re,sqlite3,time,unicodedata
from contextlib import contextmanager

@contextmanager
def sqlite_session(path):
    conn = sqlite3.connect(str(path), timeout=10)
    try:
        with conn:
            yield conn
    finally:
        conn.close()
from pathlib import Path
from structural_semantic_consistency_v023359 import parse,clean

def candidates_from_text(text,concept):
    """Only extract syntactically explicit, complete sentences from source text."""
    lines=re.split(r"[\r\n。]+",str(text or ""))
    items=[]
    for line in lines:
        sentence=clean(line)
        structure=parse(sentence)
        if structure and structure[1]==clean(concept) and sentence not in items:
            items.append(sentence)
    return items

class CandidateStore:
    def __init__(self,path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with sqlite_session(self.path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS candidates(
                token TEXT PRIMARY KEY,context TEXT NOT NULL,concept TEXT NOT NULL,
                statement TEXT NOT NULL,source TEXT NOT NULL,source_digest TEXT NOT NULL,
                status TEXT NOT NULL,created REAL NOT NULL,reviewed REAL)""")
    def propose(self,context,concept,source_text,source):
        if not str(source).strip():raise ValueError("source_required")
        output=[]
        digest=hashlib.sha256(source_text.encode("utf8")).hexdigest()
        for statement in candidates_from_text(source_text,concept):
            token="candidate-"+hashlib.sha256(
                (str(context)+"\0"+str(concept)+"\0"+statement+"\0"+digest).encode("utf8")
            ).hexdigest()[:18]
            with sqlite_session(self.path) as db:
                db.execute("""INSERT OR IGNORE INTO candidates
                    (token,context,concept,statement,source,source_digest,status,created)
                    VALUES(?,?,?,?,?,?,'PENDING',?)""",
                    (token,context,concept,statement,source,digest,time.time()))
            output.append(token)
        return output
    def list(self,context,concept):
        with sqlite_session(self.path) as db:
            return [{"token":r[0],"statement":r[1],"status":r[2],"source":r[3],
                     "source_digest":r[4]} for r in db.execute(
                """SELECT token,statement,status,source,source_digest FROM candidates
                   WHERE context=? AND concept=? ORDER BY created,token""",
                (context,concept))]
    def review(self,context,concept,token,decision):
        if decision not in {"APPROVED","REJECTED"}:raise ValueError("invalid_review")
        with sqlite_session(self.path) as db:
            cur=db.execute("""UPDATE candidates SET status=?,reviewed=?
                WHERE token=? AND context=? AND concept=? AND status='PENDING'""",
                (decision,time.time(),token,context,concept))
            return cur.rowcount==1

def render_candidates(rows):
    if not rows:return "[候補なし] 原文から対応する構造命題を抽出できませんでした。"
    return "\n".join(f"{r['token']} [{r['status']}] {r['statement']} / source={r['source']}"
                     for r in rows)
