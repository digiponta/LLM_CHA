"""Opt-in session reference memory for chat.py; separate from factual Semantic Memory.

SQLite transactions guard candidate creation/approval; candidate expiry checked
inside the same BEGIN IMMEDIATE transaction as approval. No /sleep internalization.
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime,timezone,timedelta
from pathlib import Path
from natural_confirmation_lifecycle_v023349 import GuardedConfirmationBridge,YES,NO,normalized

DDL="""CREATE TABLE IF NOT EXISTS reference_candidates (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 context TEXT NOT NULL, subject TEXT NOT NULL, slot TEXT NOT NULL,
 value TEXT NOT NULL, version INTEGER NOT NULL,
 status TEXT NOT NULL, expires_at TEXT NOT NULL,
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reference_versions (
 context TEXT NOT NULL, subject TEXT NOT NULL, slot TEXT NOT NULL,
 version INTEGER NOT NULL,
 PRIMARY KEY(context,subject,slot)
);"""
def now():return datetime.now(timezone.utc)
class SessionReferenceStore:
    def __init__(self,path,clock=now,ttl_hours=1):
        self.path=str(Path(path));Path(self.path).parent.mkdir(parents=True,exist_ok=True)
        self.clock=clock;self.ttl=timedelta(hours=ttl_hours)
        if ttl_hours<=0:raise ValueError("ttl_hours must be positive")
        with self.db() as db:db.executescript(DDL)
    @contextmanager
    def db(self):
        db=sqlite3.connect(self.path,timeout=15,isolation_level=None)
        try:
            db.execute("PRAGMA busy_timeout=15000")
            yield db
            if db.in_transaction:db.commit()
        except BaseException:
            if db.in_transaction:db.rollback()
            raise
        finally:db.close()
    def propose(self,context,subject,slot,value):
        if not all((context,subject,slot,value)):raise ValueError("invalid reference candidate")
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            old=db.execute("SELECT version FROM reference_versions WHERE context=? AND subject=? AND slot=?",
                (context,subject,slot)).fetchone()
            version=(old[0] if old else 0)+1
            db.execute("""INSERT INTO reference_versions VALUES(?,?,?,?)
                ON CONFLICT(context,subject,slot) DO UPDATE SET version=excluded.version""",
                (context,subject,slot,version))
            db.execute("""UPDATE reference_candidates SET status='superseded'
                WHERE context=? AND subject=? AND slot=? AND status='pending'""",(context,subject,slot))
            stamp=self.clock()
            cur=db.execute("""INSERT INTO reference_candidates
                (context,subject,slot,value,version,status,expires_at,created_at)
                VALUES(?,?,?,?,?,'pending',?,?)""",
                (context,subject,slot,value,version,(stamp+self.ttl).isoformat(),stamp.isoformat()))
            db.commit()
            return f"ref-{cur.lastrowid}-v{version}"
    def _record(self,db,id):
        import re
        m=re.fullmatch(r"ref-(\d+)-v(\d+)",str(id))
        if not m:return None
        row=db.execute("""SELECT id,context,subject,slot,value,version,status,expires_at
            FROM reference_candidates WHERE id=? AND version=?""",(int(m[1]),int(m[2]))).fetchone()
        return row
    def _transition(self,id,target):
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            row=self._record(db,id)
            if not row or row[6]!="pending":db.rollback();raise ValueError("candidate not pending")
            latest=db.execute("""SELECT version FROM reference_versions WHERE context=? AND subject=? AND slot=?""",
                row[1:4]).fetchone()
            if not latest or latest[0]!=row[5]:db.rollback();raise ValueError("candidate superseded")
            if self.clock()>=datetime.fromisoformat(row[7]):
                db.execute("UPDATE reference_candidates SET status='expired' WHERE id=?",(row[0],))
                db.commit();raise ValueError("candidate expired")
            if target=="approved":
                db.execute("""UPDATE reference_candidates SET status='superseded'
                    WHERE context=? AND subject=? AND slot=? AND status='approved'""",row[1:4])
            changed=db.execute("UPDATE reference_candidates SET status=? WHERE id=? AND status='pending'",
                (target,row[0])).rowcount
            db.commit()
            if changed!=1:raise ValueError("candidate transition lost")
    def approve(self,id):self._transition(id,"approved")
    def reject(self,id):
        try:self._transition(id,"rejected")
        except ValueError:
            # Rejection must not resurrect expired or superseded records.
            with self.db() as db:
                db.execute("BEGIN IMMEDIATE")
                row=self._record(db,id)
                if row and row[6]=="pending":
                    db.execute("UPDATE reference_candidates SET status='expired' WHERE id=?",(row[0],))
                db.commit()
    def lookup(self,context,subject,slot):
        with self.db() as db:
            row=db.execute("""SELECT c.value,c.expires_at,c.version,v.version
                FROM reference_candidates c JOIN reference_versions v
                ON c.context=v.context AND c.subject=v.subject AND c.slot=v.slot
                WHERE c.context=? AND c.subject=? AND c.slot=? AND c.status='approved'
                ORDER BY c.version DESC LIMIT 1""",(context,subject,slot)).fetchone()
            return row[0] if row and row[2]==row[3] and self.clock()<datetime.fromisoformat(row[1]) else None
    def recover_pending(self,context):
        """Discard orphaned unconfirmed candidates after process restart.

        Approved references remain intact. New candidate creation always
        allocates a newer version, so stale candidate tokens cannot approve.
        """
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            count=db.execute("""UPDATE reference_candidates SET status='abandoned'
                WHERE context=? AND status='pending'""",(context,)).rowcount
            db.commit()
            return count

    def invalidate(self,context,subject,slot):
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("""UPDATE reference_candidates SET status='superseded'
                WHERE context=? AND subject=? AND slot=? AND status IN ('approved','pending')""",
                (context,subject,slot))
            db.commit()

class RuntimeReferenceBridge(GuardedConfirmationBridge):
    def receive(self,text,context):
        pending=self._resolver(context).pending
        if pending and pending.get("candidate") and normalized(text) in YES|NO:
            # Reject invalid time-scoped approvals without crashing the chat loop.
            try:return super().receive(text,context)
            except ValueError:
                self._resolver(context).clear()
                return {"status":"expired","route":"reference_resolution",
                        "response":"以前の確認候補は無効です。対象をもう一度指定してください。"}
        return super().receive(text,context)

def is_reference_request(text):
    from real_dss_reference_bridge_v023339 import RealDSSBridge
    return RealDSSBridge._is_reference(text)

def handle_reference_input(bridge,text,context):
    """Return None to fall through to normal model generation."""
    pending=bridge._resolver(context).pending
    if not pending and not is_reference_request(text):return None
    return bridge.receive(text,context)

def render_reference_reply(result):
    status=result["status"]
    if result.get("response"):return result["response"]
    if status=="confirm":return f"対象は {result['value']} で合っていますか？（はい／いいえ）"
    if status=="resolved":return f"参照対象を {result['value']} として承認しました。"
    if status=="rejected":return "候補を取り消しました。"
    if status=="cancelled":return "確認をキャンセルしました。"
    if status=="expired":return "確認候補の期限が切れました。もう一度指定してください。"
    if status=="no_confirmation_pending":return "現在、承認待ちの候補はありません。"
    if status=="abstain":return "対象を特定できませんでした。もう一度指定してください。"
    if status=="confirm_required":return "確認待ちです。「はい」か「いいえ」で回答してください。"
    return None
