import tempfile,unittest
from pathlib import Path
from clarification_interruption_v023340 import InterruptibleDSSBridge
from semantic_candidate_adapter_v023337 import JsonCandidateStore

class InterruptTests(unittest.TestCase):
    def setUp(self):
        self.dir=tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.memory=JsonCandidateStore(Path(self.dir.name)/"shadow.json")
        self.b=InterruptibleDSSBridge(self.memory)
    def test_reported_regression(self):
        self.assertEqual(self.b.receive("昨日の実験の続きをやって","B")["status"],"clarify")
        r=self.b.receive("AIを開発したい","B")
        self.assertEqual(r["route"],"real_dss")
        self.assertEqual(r["purpose"],"development")
        self.assertEqual(r["interruption"],"new_explicit_goal")
        self.assertIsNone(self.b._resolver("B").pending)
    def test_proposed_candidate_rejected_on_switch(self):
        self.b.receive("昨日の実験の続きをやって","B")
        self.b.receive("cursor","B")
        r=self.b.receive("それよりLLMを勉強したい","B")
        self.assertEqual(r["route"],"real_dss")
        self.assertIsNone(self.memory.lookup("B","experiment","target"))
        self.assertEqual([x["status"] for x in self.memory._read()["records"]],["rejected"])
    def test_confirmation_works(self):
        self.b.receive("昨日の実験の続きをやって","C")
        self.assertEqual(self.b.receive("cursor","C")["status"],"confirm")
        self.assertEqual(self.b.confirm(True,"C")["status"],"resolved")
        self.assertEqual(self.b.receive("前回の実験の続きをやって","C")["value"],"cursor")
    def test_ambiguous_answer_keeps_pending(self):
        self.b.receive("昨日の実験の続きをやって","A")
        self.assertEqual(self.b.receive("ちょっと考えて","A")["status"],"clarify")
        self.assertIsNotNone(self.b._resolver("A").pending)
    def test_cancel(self):
        self.b.receive("昨日の実験の続きをやって","A")
        self.assertEqual(self.b.receive("キャンセル","A")["status"],"cancelled")
    def test_other_context_unchanged(self):
        self.b.receive("昨日の実験の続きをやって","A")
        r=self.b.receive("LLMを勉強したい","B")
        self.assertEqual(r["route"],"real_dss")
        self.assertIsNotNone(self.b._resolver("A").pending)
if __name__=="__main__":unittest.main()
