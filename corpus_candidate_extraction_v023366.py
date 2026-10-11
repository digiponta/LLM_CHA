"""v0.2.33.66: read-only corpus-scoped proposition candidate extraction.

Byte offsets refer to immutable UTF-8 bytes of the *whole* file. The candidate
store is independent of semantic memory and Truth State, and all entries start
PENDING. A reviewer decision is not verification of objective truth.
"""
from pathlib import Path
import hashlib,sqlite3,time,re
from structural_semantic_consistency_v023359 import parse,clean

def scan_corpus(path,concept,limit=100):
    if not 1<=limit<=1000:raise ValueError("limit_out_of_range")
    path=Path(path).resolve()
    content=path.read_bytes()
    raw_digest=hashlib.sha256(content).hexdigest()
    text=content.decode("utf-8")  # fail on invalid UTF-8; no lossy offsets
    results=[]
    # Spans preserve original file byte positions (UTF-8), not character indices.
    for m in re.finditer(r"[^。\r\n]+(?:。|(?=\r|\n|$))",text):
        original=m.group()
        statement=clean(original)
        p=parse(statement)
        if p is None or p[1]!=clean(concept):continue
        start=len(text[:m.start()].encode("utf-8"))
        end=len(text[:m.end()].encode("utf-8"))
        snippet=content[start:end]
        results.append({"statement":statement,"start_byte":start,"end_byte":end,
                        "snippet_sha256":hashlib.sha256(snippet).hexdigest(),
                        "file_sha256":raw_digest,"source_path":str(path)})
        if len(results)>=limit:break
    return results

class CorpusCandidateStore:
    def __init__(self,path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with sqlite3.connect(self.path) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS corpus_candidates(
                token TEXT PRIMARY KEY, context TEXT NOT NULL, concept TEXT NOT NULL,
                statement TEXT NOT NULL, source_path TEXT NOT NULL,
                file_sha256 TEXT NOT NULL, start_byte INTEGER NOT NULL,
                end_byte INTEGER NOT NULL, snippet_sha256 TEXT NOT NULL,
                status TEXT NOT NULL, created REAL NOT NULL, reviewed REAL)""")
    def propose_from_file(self,context,concept,path,limit=100):
        spans=scan_corpus(path,concept,limit)
        tokens=[]
        with sqlite3.connect(self.path) as conn:
            for span in spans:
                seed="\0".join(str(x) for x in
                    (context,concept,span["source_path"],span["file_sha256"],
                     span["start_byte"],span["end_byte"],span["statement"]))
                token="corpus-"+hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]
                conn.execute("""INSERT OR IGNORE INTO corpus_candidates(
                    token,context,concept,statement,source_path,file_sha256,
                    start_byte,end_byte,snippet_sha256,status,created)
                    VALUES(?,?,?,?,?,?,?,?,?,'PENDING',?)""",
                    (token,context,concept,span["statement"],span["source_path"],
                     span["file_sha256"],span["start_byte"],span["end_byte"],
                     span["snippet_sha256"],time.time()))
                tokens.append(token)
        return tokens
    def list(self,context,concept):
        with sqlite3.connect(self.path) as conn:
            rows=conn.execute("""SELECT token,statement,status,source_path,file_sha256,
                start_byte,end_byte,snippet_sha256 FROM corpus_candidates
                WHERE context=? AND concept=? ORDER BY start_byte,token""",(context,concept)).fetchall()
        return [dict(zip(("token","statement","status","source_path","file_sha256",
                          "start_byte","end_byte","snippet_sha256"),r)) for r in rows]
    def verify_source(self,row):
        try:
            data=Path(row["source_path"]).read_bytes()
        except OSError:return False
        if hashlib.sha256(data).hexdigest()!=row["file_sha256"]:return False
        snippet=data[row["start_byte"]:row["end_byte"]]
        return hashlib.sha256(snippet).hexdigest()==row["snippet_sha256"]
    def review(self,context,concept,token,decision):
        if decision not in {"APPROVED","REJECTED"}:raise ValueError("invalid_review")
        record=next((r for r in self.list(context,concept) if r["token"]==token),None)
        if record is None or record["status"]!="PENDING" or not self.verify_source(record):
            return False
        with sqlite3.connect(self.path) as conn:
            cur=conn.execute("""UPDATE corpus_candidates SET status=?,reviewed=?
                WHERE token=? AND context=? AND concept=? AND status='PENDING'""",
                (decision,time.time(),token,context,concept))
            return cur.rowcount==1

def render_corpus_candidates(rows):
    if not rows:return "[候補なし] 一致する構造命題はありません。"
    return "\n".join(f"{r['token']} [{r['status']}] {r['statement']} "
                     f"bytes={r['start_byte']}:{r['end_byte']} "
                     f"sha256={r['file_sha256'][:12]}…" for r in rows)
