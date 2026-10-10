import tempfile,unittest
from pathlib import Path
from clarification_normalization_v023343 import classify,NormalizedClarificationBridge
from semantic_candidate_adapter_v023337 import JsonCandidateStore
from heldout_clarification_eval_v023342 import PROBES,EXPECTED_STATUS

class NormalizationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store=JsonCandidateStore(Path(self.temp.name)/"shadow.json")
        self.bridge=NormalizedClarificationBridge(self.store)
    def test_labels(self):
        self.assertEqual(classify("カーソルの方")["canonical"],"cursor")
        self.assertEqual(classify("意味記憶の実験")["canonical"],"semantic_memory")
        self.assertEqual(classify("別件を先に相談したい")["intent"],"SWITCH")
        self.assertEqual(classify("分からない")["intent"],"UNCERTAIN")
    def test_alias_requires_confirmation(self):
        self.bridge.receive("昨日の実験の続きをやって","A")
        self.assertEqual(self.bridge.receive("カーソルの方","A")["status"],"confirm")
        self.assertIsNone(self.store.lookup("A","experiment","target"))
        self.assertEqual(self.bridge.confirm(True,"A")["value"],"cursor")
    def test_indirect_switch(self):
        self.bridge.receive("昨日の実験の続きをやって","A")
        r=self.bridge.receive("別件を先に相談したい","A")
        self.assertEqual(r["route"],"real_dss")
        self.assertEqual(r["interruption"],"indirect_switch")
        self.assertIsNone(self.bridge._resolver("A").pending)
    def test_negation_does_not_pick_answer(self):
        self.assertEqual(classify("カーソルではない")["intent"],"UNCERTAIN")
        self.assertEqual(classify("意味記憶じゃなくてカーソル")["intent"],"UNCERTAIN")
    def test_heldout_comparison_no_autoapproval(self):
        for id,first,second,expected_route in PROBES:
            with self.subTest(id=id):
                with tempfile.TemporaryDirectory() as td:
                    store=JsonCandidateStore(Path(td)/"test.json")
                    b=NormalizedClarificationBridge(store)
                    b.receive(first,"case")
                    result=b.receive(second,"case")
                    self.assertEqual(result["route"],expected_route)
                    self.assertEqual(result["status"],EXPECTED_STATUS[id])
                    self.assertEqual(sum(r["status"]=="approved" for r in store._read()["records"]),0)
if __name__=="__main__":unittest.main()
