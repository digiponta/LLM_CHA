import tempfile,unittest
from pathlib import Path
from unittest.mock import Mock
from runtime_reference_integration_v023352 import SessionReferenceStore,RuntimeReferenceBridge
from truth_aware_reference_bridge_v023355 import TruthAwareReferenceBridge,render_truth_reference_result

class TruthAwareReferenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store=SessionReferenceStore(Path(self.tmp.name)/"refs.db")
        self.runtime=RuntimeReferenceBridge(self.store)
    def approve(self):
        for t in ("昨日の実験の続きをやって","cursor","はい"):
            self.runtime.receive(t,"A")
    def semantic(self,state="KNOWN",truth_state="UNVERIFIED",answer="参照に関する回答",action="ANSWER"):
        x=Mock()
        x.state=state;x.truth_state=truth_state;x.answer=answer
        x.action=action;x.provenance="test-fixture"
        semantic=Mock()
        semantic.resolve.return_value=x
        return semantic
    def test_no_reference_must_not_query(self):
        sem=self.semantic()
        r=TruthAwareReferenceBridge(self.store,sem).lookup("A")
        self.assertEqual(r["status"],"no_approved_reference")
        sem.resolve.assert_not_called()
    def test_unverified_suppressed(self):
        self.approve();sem=self.semantic()
        r=TruthAwareReferenceBridge(self.store,sem).lookup("A")
        sem.resolve.assert_called_once_with("cursorとは")
        self.assertEqual(r["status"],"review_required")
        self.assertEqual(r["answer"],"")
        self.assertNotIn("参照に関する回答",render_truth_reference_result(r))
    def test_false_contested_outdated_suppressed(self):
        self.approve()
        for state in ("FALSE","CONTESTED","OUTDATED","UNVERIFIED"):
            with self.subTest(state=state):
                r=TruthAwareReferenceBridge(self.store,self.semantic(truth_state=state)).lookup("A")
                self.assertEqual(r["status"],"review_required")
    def test_explicit_true(self):
        self.approve()
        r=TruthAwareReferenceBridge(self.store,self.semantic(truth_state="TRUE")).lookup("A")
        self.assertEqual(r["status"],"trusted_evidence")
        self.assertIn("test-fixture",render_truth_reference_result(r))
    def test_unknown_even_if_true(self):
        self.approve()
        r=TruthAwareReferenceBridge(self.store,self.semantic(state="UNKNOWN",truth_state="TRUE")).lookup("A")
        self.assertEqual(r["status"],"review_required")
    def test_cross_context(self):
        self.approve();sem=self.semantic(truth_state="TRUE")
        r=TruthAwareReferenceBridge(self.store,sem).lookup("B")
        self.assertEqual(r["status"],"no_approved_reference")
        sem.resolve.assert_not_called()

if __name__=="__main__":unittest.main()
