import tempfile,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from runtime_reference_integration_v023352 import (
    SessionReferenceStore,RuntimeReferenceBridge,handle_reference_input,render_reference_reply
)
class Clock:
    def __init__(self):self.t=datetime(2026,10,10,tzinfo=timezone.utc)
    def __call__(self):return self.t
class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.clock=Clock()
        self.path=Path(self.tmp.name)/"reference.sqlite3"
        self.store=SessionReferenceStore(self.path,clock=self.clock)
        self.bridge=RuntimeReferenceBridge(self.store)
    def test_user_facing_confirmation(self):
        r=handle_reference_input(self.bridge,"昨日の実験の続きをやって","A")
        self.assertEqual(r["status"],"clarify")
        r=handle_reference_input(self.bridge,"カーソルでお願いします","A")
        self.assertEqual(r["status"],"confirm")
        self.assertIn("はい",render_reference_reply(r))
        self.assertIsNone(self.store.lookup("A","experiment","target"))
        r=handle_reference_input(self.bridge,"はい","A")
        self.assertEqual(r["status"],"resolved")
        self.assertEqual(self.store.lookup("A","experiment","target"),"cursor")
    def test_context_and_invalidation(self):
        for text in ("昨日の実験の続きをやって","cursor","はい"):
            handle_reference_input(self.bridge,text,"A")
        self.assertIsNone(self.store.lookup("B","experiment","target"))
        self.assertEqual(handle_reference_input(self.bridge,"前回の実験を再開して","B")["status"],"clarify")
        self.bridge.invalidate("A")
        self.assertIsNone(self.store.lookup("A","experiment","target"))
    def test_expiry(self):
        for text in ("昨日の実験の続きをやって","cursor"):
            handle_reference_input(self.bridge,text,"A")
        self.clock.t+=timedelta(hours=2)
        result=handle_reference_input(self.bridge,"はい","A")
        self.assertEqual(result["status"],"expired")
        self.assertIsNone(self.store.lookup("A","experiment","target"))
    def test_replay_and_default_fallthrough(self):
        self.assertIsNone(handle_reference_input(self.bridge,"量子力学とは","A"))
        self.assertIsNone(handle_reference_input(self.bridge,"はい","A"))
        for text in ("昨日の実験の続きをやって","cursor","はい"):
            handle_reference_input(self.bridge,text,"A")
        self.assertIsNone(handle_reference_input(self.bridge,"はい","A"))
    def test_stale_candidate(self):
        a=self.store.propose("A","experiment","target","cursor")
        b=self.store.propose("A","experiment","target","semantic_memory")
        with self.assertRaises(ValueError):self.store.approve(a)
        self.store.approve(b)
        self.assertEqual(self.store.lookup("A","experiment","target"),"semantic_memory")
    def test_no_factual_memory_write(self):
        self.assertTrue(self.path.exists())
        self.assertEqual(len(list(Path(self.tmp.name).iterdir())),1)
if __name__=="__main__":unittest.main()
