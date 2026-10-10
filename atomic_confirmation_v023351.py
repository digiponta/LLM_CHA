"""v0.2.33.51 — atomic candidate version/CAS prototype.

SQLite BEGIN IMMEDIATE serializes mutations across connections and processes.
Standalone experiment, not wired into chat.py or production Semantic Memory.
"""
import argparse,concurrent.futures,json,sqlite3,tempfile,threading
from contextlib import contextmanager
from pathlib import Path

SCHEMA="""CREATE TABLE IF NOT EXISTS candidates(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 context TEXT NOT NULL, subject TEXT NOT NULL, slot TEXT NOT NULL,
 value TEXT NOT NULL, version INTEGER NOT NULL, status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS revisions(
 context TEXT NOT NULL, subject TEXT NOT NULL, slot TEXT NOT NULL,
 version INTEGER NOT NULL, PRIMARY KEY(context,subject,slot)
);"""
class AtomicStore:
    def __init__(self,path):
        self.path=str(path)
        with self._db() as db:db.executescript(SCHEMA)
    @contextmanager
    def _db(self):
        # sqlite3.Connection.__exit__ commits/rolls back, but does NOT close.
        # An open SQLite handle prevents TemporaryDirectory cleanup on Windows.
        db=sqlite3.connect(self.path,timeout=15,isolation_level=None)
        try:
            db.execute("PRAGMA busy_timeout=15000")
            yield db
            if db.in_transaction:
                db.commit()
        except BaseException:
            if db.in_transaction:
                db.rollback()
            raise
        finally:
            db.close()
    def propose(self,context,subject,slot,value):
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            row=db.execute("SELECT version FROM revisions WHERE context=? AND subject=? AND slot=?",
                           (context,subject,slot)).fetchone()
            version=(row[0] if row else 0)+1
            db.execute("""INSERT INTO revisions(context,subject,slot,version) VALUES(?,?,?,?)
                ON CONFLICT(context,subject,slot) DO UPDATE SET version=excluded.version""",
                (context,subject,slot,version))
            db.execute("""UPDATE candidates SET status='superseded'
                WHERE context=? AND subject=? AND slot=? AND status='pending'""",
                (context,subject,slot))
            cur=db.execute("""INSERT INTO candidates(context,subject,slot,value,version,status)
                VALUES(?,?,?,?,?,'pending')""",(context,subject,slot,value,version))
            db.commit()
            return {"candidate_id":cur.lastrowid,"version":version}
    def transition(self,context,candidate_id,version,target):
        if target not in ("approved","rejected","expired"):raise ValueError("invalid transition")
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            row=db.execute("""SELECT context,subject,slot,version,status FROM candidates
                                 WHERE id=?""",(candidate_id,)).fetchone()
            if not row or row[0]!=context or row[3]!=version or row[4]!="pending":
                db.rollback();return False
            current=db.execute("""SELECT version FROM revisions
                WHERE context=? AND subject=? AND slot=?""",(row[0],row[1],row[2])).fetchone()
            if not current or current[0]!=version:db.rollback();return False
            changed=db.execute("""UPDATE candidates SET status=? WHERE id=? AND version=? AND status='pending'""",
                (target,candidate_id,version)).rowcount
            db.commit()
            return changed==1
    def status(self,candidate_id):
        with self._db() as db:
            row=db.execute("SELECT status FROM candidates WHERE id=?",(candidate_id,)).fetchone()
            return row[0] if row else None
    def approved(self,context,subject,slot):
        with self._db() as db:
            return db.execute("""SELECT value FROM candidates WHERE context=? AND subject=? AND slot=?
                AND status='approved' ORDER BY version DESC LIMIT 1""",(context,subject,slot)).fetchone()

def evaluate():
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/"cas.sqlite";s=AtomicStore(path)
        results=[]
        def check(name,passed,detail):
            results.append({"id":name,"passed":bool(passed),"detail":detail})
        a=s.propose("A","experiment","target","cursor")
        b=s.propose("A","experiment","target","semantic_memory")
        stale=s.transition("A",a["candidate_id"],a["version"],"approved")
        ok=s.transition("A",b["candidate_id"],b["version"],"approved")
        check("stale_version",not stale and ok and s.status(a["candidate_id"])=="superseded",
              {"stale_accepted":stale,"latest_accepted":ok})
        repeated=s.transition("A",b["candidate_id"],b["version"],"approved")
        check("double_approval",not repeated,{"repeat_accepted":repeated})
        c=s.propose("B","experiment","target","cursor")
        cross=s.transition("A",c["candidate_id"],c["version"],"approved")
        check("cross_context",not cross,{"cross_accepted":cross})
        d=s.propose("A","other","target","cursor")
        rejected=s.transition("A",d["candidate_id"],d["version"],"rejected")
        invalid=s.transition("A",d["candidate_id"],d["version"],"approved")
        check("reject_is_terminal",rejected and not invalid,{"rejected":rejected,"late_approved":invalid})
        e=s.propose("A","other","target","semantic_memory")
        expired=s.transition("A",e["candidate_id"],e["version"],"expired")
        check("expire_is_terminal",expired and not s.transition("A",e["candidate_id"],e["version"],"approved"),
              {"expired":expired})
        f=s.propose("C","experiment","target","cursor")
        # Separate connections, concurrent requests for one candidate.
        gate=threading.Barrier(2)
        def worker(_):
            store=AtomicStore(path)
            gate.wait(timeout=10)
            return store.transition("C",f["candidate_id"],f["version"],"approved")
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            outcomes=list(pool.map(worker,range(2)))
        check("concurrent_same_candidate",sum(outcomes)==1,
              {"attempts":outcomes,"approved_count":sum(outcomes)})
        g=s.propose("D","experiment","target","cursor")
        new=s.propose("D","experiment","target","semantic_memory")
        old_result=s.transition("D",g["candidate_id"],g["version"],"approved")
        new_result=s.transition("D",new["candidate_id"],new["version"],"approved")
        check("candidate_replacement",not old_result and new_result,
              {"old":old_result,"new":new_result})
        return {"version":"v0.2.33.51","passed":sum(r["passed"] for r in results),
                "total":len(results),"cases":results,
                "scope":["SQLite-backed atomic prototype, not existing JsonCandidateStore",
                    "No process-level stress test or timing/TTL integration",
                    "Confirmation tokens require exact candidate_id+version and context",
                    "No production integration"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="results/atomic_confirmation_v023351.json")
    a=p.parse_args();path=Path(a.out)
    if path.exists():raise FileExistsError("Refusing overwrite")
    result=evaluate();path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps({"passed":result["passed"],"total":result["total"],"cases":result["cases"]},ensure_ascii=False,indent=2))
    print("Saved",path)
if __name__=="__main__":main()
