import json
from pathlib import Path
import tempfile
import unittest

from corpus_restore_adapter_v023342 import restore_from_corpus, current_subjects_for_snapshot
from longterm_context_v02340 import ContextCheckpoint
from proposition_truth_v0233827 import TruthOverlay, proposition_id
from retrieval_first_runtime_v1012161 import resolve_subject
from grounded_expansion_v0233826 import PropositionCursor

SUBJECT="宇宙"
def make_corpus(path, statement="宇宙は広大", subject=SUBJECT):
    row={"subject":subject,"statement":statement,"relation":"is",
         "object_description":"","source_text":statement,"source":"fixture"}
    path.write_text(json.dumps(row,ensure_ascii=False)+"\n",encoding="utf-8")

class CorpusRestoreAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/"corpus.jsonl"
        make_corpus(self.path)
        hit=resolve_subject(self.path,SUBJECT)
        self.assertTrue(hit.hit)
        self.pid=proposition_id(SUBJECT,"宇宙は広大",hit.provenance)
        c=ContextCheckpoint()
        c.remember(SUBJECT,self.pid)
        self.snapshot=c.export()

    def test_current_corpus_retained(self):
        r=restore_from_corpus(self.snapshot,self.path,lambda _:("TRUE",True),TruthOverlay())
        self.assertEqual((r.retained,r.rejected),(1,0))

    def test_subject_false_denied_even_when_gate_claims_true(self):
        r=restore_from_corpus(self.snapshot,self.path,lambda _:("FALSE",True),TruthOverlay())
        self.assertEqual(r.retained,0)

    def test_subject_gate_denied(self):
        r=restore_from_corpus(self.snapshot,self.path,lambda _:("TRUE",False),TruthOverlay())
        self.assertEqual(r.retained,0)

    def test_overlay_outdated(self):
        overlay=TruthOverlay()
        overlay.rows[self.pid]=("OUTDATED","review")
        r=restore_from_corpus(self.snapshot,self.path,lambda _:("TRUE",True),overlay)
        self.assertEqual(r.retained,0)

    def test_corpus_changed(self):
        make_corpus(self.path,"宇宙は更新された")
        r=restore_from_corpus(self.snapshot,self.path,lambda _:("TRUE",True),TruthOverlay())
        self.assertEqual(r.retained,0)

    def test_corpus_deleted_subject(self):
        make_corpus(self.path,"宇宙は広大",subject="GPU")
        r=restore_from_corpus(self.snapshot,self.path,lambda _:("TRUE",True),TruthOverlay())
        self.assertEqual(r.retained,0)

    def test_corpus_missing_fails(self):
        self.path.unlink()
        with self.assertRaises(FileNotFoundError):
            restore_from_corpus(self.snapshot,self.path,lambda _:("TRUE",True),TruthOverlay())

    def test_gate_missing_state_fails(self):
        with self.assertRaises(ValueError):
            restore_from_corpus(self.snapshot,self.path,lambda _:("",True),TruthOverlay())

    def test_composed_propositions(self):
        make_corpus(self.path,"宇宙は広大 / 宇宙は膨張")
        lookup=resolve_subject(self.path,SUBJECT)
        parts=PropositionCursor.split(lookup.answer)
        self.assertEqual(len(parts),2)
        c=ContextCheckpoint()
        for p in parts:
            c.remember(SUBJECT,proposition_id(SUBJECT,p,lookup.provenance))
        r=restore_from_corpus(c.export(),self.path,lambda _:("TRUE",True),TruthOverlay())
        self.assertEqual(r.retained,2)

    def test_explicit_unverified_only_when_gate_permits(self):
        self.assertEqual(restore_from_corpus(self.snapshot,self.path,lambda _:("UNVERIFIED",True),TruthOverlay()).retained,1)
        self.assertEqual(restore_from_corpus(self.snapshot,self.path,lambda _:("UNVERIFIED",False),TruthOverlay()).retained,0)

if __name__=="__main__":
    unittest.main()
