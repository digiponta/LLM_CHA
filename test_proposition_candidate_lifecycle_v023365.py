import tempfile,unittest
from pathlib import Path
from proposition_candidate_lifecycle_v023365 import CandidateStore,candidates_from_text

class CandidateLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=CandidateStore(Path(self.tmp.name)/"candidates.sqlite3")
    def test_extract_matching_concept_only(self):
        self.assertEqual(candidates_from_text("GPUは並列計算に適する。AはBを含む。","GPU"),
                         ["GPUは並列計算に適する"])
    def test_unsupported_grammar_fails_closed(self):
        self.assertEqual(candidates_from_text("量子力学について説明する文章","量子力学"),[])
    def test_propose_pending(self):
        tokens=self.store.propose("s1","GPU","GPUは並列計算に適する。","reviewed-source")
        self.assertEqual(len(tokens),1)
        self.assertEqual(self.store.list("s1","GPU")[0]["status"],"PENDING")
    def test_explicit_approval_not_truth(self):
        token=self.store.propose("s1","GPU","GPUは並列計算に適する","user")[0]
        self.assertTrue(self.store.review("s1","GPU",token,"APPROVED"))
        self.assertEqual(self.store.list("s1","GPU")[0]["status"],"APPROVED")
        self.assertFalse(self.store.review("s1","GPU",token,"APPROVED"))
    def test_rejection(self):
        token=self.store.propose("s1","GPU","GPUは並列計算に適する","user")[0]
        self.assertTrue(self.store.review("s1","GPU",token,"REJECTED"))
    def test_context_isolated(self):
        token=self.store.propose("s1","GPU","GPUは並列計算に適する","user")[0]
        self.assertFalse(self.store.review("s2","GPU",token,"APPROVED"))
        self.assertEqual(self.store.list("s2","GPU"),[])
    def test_concept_isolated(self):
        token=self.store.propose("s1","GPU","GPUは並列計算に適する","user")[0]
        self.assertFalse(self.store.review("s1","CPU",token,"APPROVED"))
    def test_dedup(self):
        a=self.store.propose("s1","GPU","GPUは並列計算に適する","user")
        b=self.store.propose("s1","GPU","GPUは並列計算に適する","user")
        self.assertEqual(a,b)
        self.assertEqual(len(self.store.list("s1","GPU")),1)
    def test_source_required(self):
        with self.assertRaises(ValueError):
            self.store.propose("s1","GPU","GPUは並列計算に適する","")
    def test_no_semantic_writes(self):
        self.store.propose("s1","GPU","GPUは並列計算に適する","source")
        self.assertEqual(sorted(p.name for p in Path(self.tmp.name).iterdir()),
                         ["candidates.sqlite3"])
if __name__=="__main__":unittest.main()
