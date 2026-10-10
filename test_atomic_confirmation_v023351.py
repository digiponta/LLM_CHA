import tempfile,unittest
from pathlib import Path
from atomic_confirmation_v023351 import AtomicStore,evaluate
class AtomicConfirmationTests(unittest.TestCase):
    def test_diagnostics(self):
        result=evaluate()
        self.assertEqual(result["total"],7)
        self.assertEqual([r for r in result["cases"] if not r["passed"]],[])
    def test_cas_rejects_stale(self):
        with tempfile.TemporaryDirectory() as td:
            store=AtomicStore(Path(td)/"test.db")
            a=store.propose("A","experiment","target","cursor")
            b=store.propose("A","experiment","target","semantic_memory")
            self.assertNotEqual(a["version"],b["version"])
            self.assertFalse(store.transition("A",a["candidate_id"],a["version"],"approved"))
            self.assertTrue(store.transition("A",b["candidate_id"],b["version"],"approved"))
            self.assertFalse(store.transition("A",b["candidate_id"],b["version"],"approved"))
    def test_context_and_terminal_state(self):
        with tempfile.TemporaryDirectory() as td:
            store=AtomicStore(Path(td)/"test.db")
            a=store.propose("A","experiment","target","cursor")
            self.assertFalse(store.transition("B",a["candidate_id"],a["version"],"approved"))
            self.assertTrue(store.transition("A",a["candidate_id"],a["version"],"rejected"))
            self.assertFalse(store.transition("A",a["candidate_id"],a["version"],"approved"))
if __name__=="__main__":unittest.main()
