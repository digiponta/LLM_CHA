import tempfile,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from semantic_candidate_adapter_v023337 import JsonCandidateStore
from dss_unknown_adapter_v023336 import IntegrationResolver,MockDSS

class ShadowMemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"candidates.json"
        self.now=datetime(2026,10,10,tzinfo=timezone.utc)
        self.clock=lambda:self.now
        self.memory=JsonCandidateStore(self.path,clock=self.clock,ttl_hours=24)
    def test_confirm_persists_restart(self):
        r=IntegrationResolver(MockDSS(),self.memory)
        self.assertEqual(r.receive("昨日の実験の続きをやって","A")["status"],"clarify")
        self.assertEqual(r.receive("cursor","A")["status"],"confirm")
        self.assertIsNone(self.memory.lookup("A","experiment","target"))
        self.assertEqual(r.confirm(True,"A")["status"],"resolved")
        again=JsonCandidateStore(self.path,clock=self.clock)
        self.assertEqual(again.lookup("A","experiment","target"),"cursor")
        self.assertIsNone(again.lookup("B","experiment","target"))
    def test_reject_not_readable(self):
        x=self.memory.propose("A","e","s","cursor")
        self.memory.reject(x)
        self.assertIsNone(self.memory.lookup("A","e","s"))
    def test_expiry_and_invalidate(self):
        x=self.memory.propose("A","e","s","cursor")
        self.memory.approve(x)
        self.assertEqual(self.memory.lookup("A","e","s"),"cursor")
        self.now+=timedelta(hours=25)
        self.assertIsNone(self.memory.lookup("A","e","s"))
        y=self.memory.propose("A","e","s","semantic_memory")
        self.memory.approve(y)
        self.memory.invalidate("A","e","s")
        self.assertIsNone(self.memory.lookup("A","e","s"))
    def test_supersede(self):
        x=self.memory.propose("A","e","s","cursor");self.memory.approve(x)
        y=self.memory.propose("A","e","s","semantic_memory");self.memory.approve(y)
        self.assertEqual(self.memory.lookup("A","e","s"),"semantic_memory")
        states=[r["status"] for r in self.memory._read()["records"]]
        self.assertEqual(states,["superseded","approved"])
    def test_expired_candidate_never_approved(self):
        x=self.memory.propose("A","e","s","cursor")
        self.now+=timedelta(hours=25)
        with self.assertRaises(ValueError):self.memory.approve(x)
        self.assertIsNone(self.memory.lookup("A","e","s"))
if __name__=="__main__":unittest.main()
