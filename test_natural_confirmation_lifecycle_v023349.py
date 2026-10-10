import tempfile,unittest
from pathlib import Path
from natural_confirmation_lifecycle_v023349 import GuardedConfirmationBridge,evaluate
from semantic_candidate_adapter_v023337 import JsonCandidateStore
class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store=JsonCandidateStore(Path(self.tmp.name)/"store.json")
        self.bridge=GuardedConfirmationBridge(self.store)
    def test_approve(self):
        self.bridge.receive("昨日の実験の続きをやって","A")
        self.bridge.receive("cursor","A")
        self.assertIsNone(self.store.lookup("A","experiment","target"))
        self.assertEqual(self.bridge.receive("はい","A")["status"],"resolved")
        self.assertEqual(self.store.lookup("A","experiment","target"),"cursor")
    def test_compound_yes_is_not_approved(self):
        self.bridge.receive("昨日の実験の続きをやって","A")
        self.bridge.receive("cursor","A")
        self.assertEqual(self.bridge.receive("はい、でも違うかも","A")["status"],"confirm_required")
        self.assertIsNone(self.store.lookup("A","experiment","target"))
    def test_reject(self):
        self.bridge.receive("昨日の実験の続きをやって","A")
        self.bridge.receive("cursor","A")
        self.assertEqual(self.bridge.receive("いいえ","A")["status"],"rejected")
        self.assertIsNone(self.store.lookup("A","experiment","target"))
    def test_context_gate(self):
        self.bridge.receive("昨日の実験の続きをやって","A")
        self.bridge.receive("cursor","A")
        self.assertEqual(self.bridge.receive("はい","B")["status"],"no_confirmation_pending")
        self.assertIsNone(self.store.lookup("A","experiment","target"))
    def test_scenarios(self):
        result=evaluate()
        self.assertEqual(result["pass_count"],result["total"])
        self.assertTrue(result["context_isolation"])
if __name__=="__main__":unittest.main()
