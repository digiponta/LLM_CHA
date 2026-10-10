import tempfile,unittest
from pathlib import Path
from real_dss_reference_bridge_v023339 import RealDSSBridge
from semantic_candidate_adapter_v023337 import JsonCandidateStore
class RealDSSBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store=JsonCandidateStore(Path(self.tmp.name)/"shadow.json")
        self.b=RealDSSBridge(self.store)
    def test_actual_dss(self):
        r=self.b.receive("LLMを勉強したい","A")
        self.assertEqual(r["route"],"real_dss")
        self.assertEqual(r["purpose"],"learning")
        self.assertEqual(r["topic"],"LLM")
    def test_clarification_not_routed_to_dss(self):
        self.assertEqual(self.b.receive("昨日の実験の続きをやって","A")["status"],"clarify")
        self.assertEqual(self.b.receive("cursor","A")["status"],"confirm")
        self.assertEqual(self.b.confirm(True,"A")["status"],"resolved")
        r=self.b.receive("前回の実験の続きをやって","A")
        self.assertEqual(r["value"],"cursor")
        self.assertNotIn("A",self.b.controllers)
    def test_context_isolation(self):
        self.b.receive("昨日の実験の続きをやって","A")
        self.b.receive("cursor","A")
        self.b.confirm(True,"A")
        self.assertEqual(self.b.receive("昨日の実験の続きをやって","B")["status"],"clarify")
        self.assertIsNone(self.store.lookup("B","experiment","target"))
    def test_invalidation(self):
        self.b.receive("昨日の実験の続きをやって","A")
        self.b.receive("cursor","A");self.b.confirm(True,"A")
        self.b.invalidate("A")
        self.assertEqual(self.b.receive("昨日の実験の続きをやって","A")["status"],"clarify")
    def test_real_dss_scoped_state(self):
        self.b.receive("LLMを勉強したい","A")
        self.b.receive("AIを開発したい","B")
        self.assertEqual(self.b.controllers["A"].purpose,"learning")
        self.assertEqual(self.b.controllers["B"].purpose,"development")
if __name__=="__main__":unittest.main()
