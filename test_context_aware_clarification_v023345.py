import tempfile,unittest
from pathlib import Path
from context_aware_clarification_v023345 import ContextAwareBridge,decide,evaluate
from semantic_candidate_adapter_v023337 import JsonCandidateStore

class ContextAwareTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store=JsonCandidateStore(Path(self.tmp.name)/"shadow.json")
        self.bridge=ContextAwareBridge(self.store)
    def test_polite_answers(self):
        self.assertEqual(decide("カーソルでお願いします")["canonical"],"cursor")
        self.assertEqual(decide("意味記憶のほうです")["canonical"],"semantic_memory")
    def test_switch(self):
        self.bridge.receive("昨日の実験の続きをやって","A")
        result=self.bridge.receive("その前に違う件を聞きたい","A")
        self.assertEqual(result["route"],"real_dss")
        self.assertEqual(result["interruption"],"context_aware_switch")
    def test_answer_never_autoapproved(self):
        self.bridge.receive("昨日の実験の続きをやって","A")
        self.assertEqual(self.bridge.receive("カーソルでお願いします","A")["status"],"confirm")
        self.assertIsNone(self.store.lookup("A","experiment","target"))
        self.assertEqual(self.bridge.confirm(True,"A")["value"],"cursor")
    def test_conflict_abstention(self):
        self.bridge.receive("昨日の実験の続きをやって","A")
        self.assertEqual(self.bridge.receive("カーソルと意味記憶の両方","A")["status"],"clarify")
        self.assertEqual(self.bridge.receive("意味記憶ではなくカーソル","A")["status"],"abstain")
        self.assertFalse(self.store._read()["records"])
    def test_dev_audit(self):
        r=evaluate()
        self.assertEqual(r["total"],6)
        self.assertEqual(r["false_approvals"],0)
        self.assertGreaterEqual(r["correct"],4)
if __name__=="__main__":unittest.main()
