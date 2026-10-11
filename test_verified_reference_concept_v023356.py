import tempfile,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from unittest.mock import Mock
from verified_reference_concept_v023356 import VerifiedConceptMapping,MappedTruthAwareBridge
from runtime_reference_integration_v023352 import SessionReferenceStore,RuntimeReferenceBridge

class TestMapping(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.clock=[datetime(2026,10,11,tzinfo=timezone.utc)]
        root=Path(self.tmp.name)
        self.m=VerifiedConceptMapping(root/"mapping.sqlite3",clock=lambda:self.clock[0],ttl_hours=1)
        self.refs=SessionReferenceStore(root/"references.sqlite3",clock=lambda:self.clock[0],ttl_hours=2)
        self.runtime=RuntimeReferenceBridge(self.refs)
    def approve_reference(self,context="A"):
        for text in ("昨日の実験の続きをやって","cursor","はい"):
            self.runtime.receive(text,context)
    def sem(self,truth="UNVERIFIED",state="KNOWN",action="ANSWER"):
        out=Mock();out.truth_state=truth;out.state=state;out.action=action
        out.answer="意味命題の回答";out.provenance="fixture"
        host=Mock();host.resolve.return_value=out
        return host
    def test_requires_explicit_mapping(self):
        self.approve_reference()
        tok=self.m.propose("A","cursor","量子力学","user explicit")
        self.assertIsNone(self.m.lookup("A","cursor"))
        h=self.sem("TRUE")
        result=MappedTruthAwareBridge(self.refs,self.m,h).lookup("A")
        self.assertEqual(result["status"],"no_approved_mapping")
        h.resolve.assert_not_called()
        self.assertTrue(self.m.approve("A",tok))
        result=MappedTruthAwareBridge(self.refs,self.m,h).lookup("A")
        h.resolve.assert_called_once_with("量子力学とは")
        self.assertEqual(result["status"],"trusted_evidence")
    def test_cross_context_and_replay(self):
        token=self.m.propose("A","cursor","量子力学","manual")
        self.assertFalse(self.m.approve("B",token))
        self.assertTrue(self.m.approve("A",token))
        self.assertFalse(self.m.approve("A",token))
        self.assertIsNone(self.m.lookup("B","cursor"))
    def test_stale_replacement(self):
        old=self.m.propose("A","cursor","量子力学","manual")
        new=self.m.propose("A","cursor","数学","manual")
        self.assertFalse(self.m.approve("A",old))
        self.assertTrue(self.m.approve("A",new))
        self.assertEqual(self.m.lookup("A","cursor")["concept"],"数学")
    def test_expiry(self):
        token=self.m.propose("A","cursor","数学","manual")
        self.clock[0]+=timedelta(hours=1)
        self.assertFalse(self.m.approve("A",token))
        self.assertIsNone(self.m.lookup("A","cursor"))
    def test_unverified_suppresses_answer(self):
        self.approve_reference()
        tok=self.m.propose("A","cursor","数学","manual")
        self.m.approve("A",tok)
        result=MappedTruthAwareBridge(self.refs,self.m,self.sem()).lookup("A")
        self.assertEqual(result["status"],"review_required")
        self.assertEqual(result["answer"],"")
    def test_invalidated_reference_blocks_bridge(self):
        self.approve_reference()
        tok=self.m.propose("A","cursor","数学","manual");self.m.approve("A",tok)
        self.runtime.invalidate("A")
        h=self.sem("TRUE")
        self.assertEqual(MappedTruthAwareBridge(self.refs,self.m,h).lookup("A")["status"],"no_approved_reference")
        h.resolve.assert_not_called()
    def test_mapping_invalidation(self):
        tok=self.m.propose("A","cursor","数学","manual");self.m.approve("A",tok)
        self.m.invalidate("A","cursor")
        self.assertIsNone(self.m.lookup("A","cursor"))

if __name__=="__main__":unittest.main()
