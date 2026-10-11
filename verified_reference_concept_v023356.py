"""v0.2.33.56 — verified, explicit reference-to-concept mappings.

Separate SQLite database/table from canonical Semantic Memory. Mapping approval
requires candidate ID, version and context, and never writes factual knowledge.
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime,timezone,timedelta
from pathlib import Path
import re
from truth_aware_reference_bridge_v023355 import render_truth_reference_result

SCHEMA="""CREATE TABLE IF NOT EXISTS concept_mappings(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 context TEXT NOT NULL, reference TEXT NOT NULL, concept TEXT NOT NULL,
 provenance TEXT NOT NULL, version INTEGER NOT NULL,
 status TEXT NOT NULL, expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS mapping_revisions(
 context TEXT NOT NULL, reference TEXT NOT NULL, version INTEGER NOT NULL,
 PRIMARY KEY(context,reference)
);"""

class VerifiedConceptMapping:
    def __init__(self,path,clock=None,ttl_hours=24):
        if ttl_hours<=0:raise ValueError("ttl_hours must be positive")
        self.path=str(Path(path))
        Path(self.path).parent.mkdir(parents=True,exist_ok=True)
        self.clock=clock or (lambda:datetime.now(timezone.utc))
        self.ttl=timedelta(hours=ttl_hours)
        with self.db() as db:db.executescript(SCHEMA)
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
    def propose(self,context,reference,concept,provenance):
        if not all([context.strip(),reference.strip(),concept.strip(),provenance.strip()]):
            raise ValueError("context, reference, concept, provenance required")
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            current=db.execute("SELECT version FROM mapping_revisions WHERE context=? AND reference=?",
                               (context,reference)).fetchone()
            version=(current[0] if current else 0)+1
            db.execute("""INSERT INTO mapping_revisions VALUES(?,?,?)
                ON CONFLICT(context,reference) DO UPDATE SET version=excluded.version""",
                       (context,reference,version))
            db.execute("""UPDATE concept_mappings SET status='superseded'
                WHERE context=? AND reference=? AND status IN ('pending','approved')""",
                       (context,reference))
            cur=db.execute("""INSERT INTO concept_mappings
                (context,reference,concept,provenance,version,status,expires_at)
                VALUES(?,?,?,?,?,'pending',?)""",
                (context,reference,concept,provenance,version,
                 (self.clock()+self.ttl).isoformat()))
            db.commit()
            return f"map-{cur.lastrowid}-v{version}"
    def approve(self,context,token):
        match=re.fullmatch(r"map-(\d+)-v(\d+)",token)
        if not match:return False
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            row=db.execute("""SELECT context,reference,version,status,expires_at
                FROM concept_mappings WHERE id=? AND version=?""",
                (int(match[1]),int(match[2]))).fetchone()
            if not row or row[0]!=context or row[3]!="pending":
                db.rollback();return False
            revision=db.execute("SELECT version FROM mapping_revisions WHERE context=? AND reference=?",
                                (row[0],row[1])).fetchone()
            if not revision or revision[0]!=row[2]:
                db.rollback();return False
            if self.clock()>=datetime.fromisoformat(row[4]):
                db.execute("UPDATE concept_mappings SET status='expired' WHERE id=?",(int(match[1]),))
                db.commit();return False
            changed=db.execute("UPDATE concept_mappings SET status='approved' WHERE id=? AND status='pending'",
                               (int(match[1]),)).rowcount
            db.commit()
            return changed==1
    def lookup(self,context,reference):
        with self.db() as db:
            row=db.execute("""SELECT m.concept,m.provenance,m.expires_at,m.version,r.version
                FROM concept_mappings m JOIN mapping_revisions r
                ON m.context=r.context AND m.reference=r.reference
                WHERE m.context=? AND m.reference=? AND m.status='approved'
                ORDER BY m.version DESC LIMIT 1""",(context,reference)).fetchone()
        if not row or row[3]!=row[4] or self.clock()>=datetime.fromisoformat(row[2]):
            return None
        return {"concept":row[0],"mapping_provenance":row[1],"version":row[3]}
    def invalidate(self,context,reference):
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("""UPDATE concept_mappings SET status='invalidated'
                WHERE context=? AND reference=? AND status IN ('pending','approved')""",
                (context,reference))
            db.commit()

class MappedTruthAwareBridge:
    def __init__(self,references,mappings,semantic):
        self.references=references;self.mappings=mappings;self.semantic=semantic
    def lookup(self,context):
        reference=self.references.lookup(context,"experiment","target")
        if reference is None:return {"status":"no_approved_reference"}
        mapping=self.mappings.lookup(context,reference)
        if mapping is None:return {"status":"no_approved_mapping","reference":reference}
        result=self.semantic.resolve(f"{mapping['concept']}とは")
        truth=str(result.truth_state or "UNVERIFIED").upper()
        state=str(result.state)
        action=str(result.action)
        provenance=str(result.provenance) if result.provenance is not None else ""
        # Fail closed for the known dispatcher blocking actions and unverified truth.
        permitted=(truth=="TRUE" and state not in ("UNKNOWN","NON_CONCEPT")
                   and action not in ("BLOCK","REJECT","UNKNOWN","ABSTAIN")
                   and bool(result.answer))
        return {"status":"trusted_evidence" if permitted else "review_required",
                "reference":reference,"concept":mapping["concept"],
                "mapping_provenance":mapping["mapping_provenance"],
                "knowledge_state":state,"truth_state":truth,
                "action":action,"provenance":provenance,
                "answer":str(result.answer) if permitted else ""}

def render_mapped_result(r):
    if r["status"]=="no_approved_reference":
        return "承認済み参照がありません。"
    if r["status"]=="no_approved_mapping":
        return f"参照先 {r['reference']} の承認済み概念対応がありません。推測による検索は行いません。"
    prefix=(f"[参照: {r['reference']} → 概念: {r['concept']} / "
            f"Mapping source: {r['mapping_provenance']} / "
            f"Knowledge: {r['knowledge_state']} / Truth: {r['truth_state']}]")
    if r["status"]=="trusted_evidence":return prefix+" "+r["answer"]
    return prefix+" 検証済みの回答がないため保留します。"
