import tempfile,unittest
from pathlib import Path
from corpus_candidate_extraction_v023366 import scan_corpus,CorpusCandidateStore

class CorpusCandidateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.src=self.root/"source.txt"
        self.src.write_text("GPUは並列計算に適する。\nCPUは逐次処理に適する。\nGPUはCUDAを含む。\n",encoding="utf8")
        self.store=CorpusCandidateStore(self.root/"candidates.db")
    def test_byte_offsets_and_source_hash(self):
        spans=scan_corpus(self.src,"GPU")
        self.assertEqual(len(spans),2)
        data=self.src.read_bytes()
        for s in spans:
            self.assertIn(s["statement"],data[s["start_byte"]:s["end_byte"]].decode("utf8"))
    def test_pending_and_dedup(self):
        x=self.store.propose_from_file("ctx","GPU",self.src)
        y=self.store.propose_from_file("ctx","GPU",self.src)
        self.assertEqual(x,y)
        self.assertEqual(len(self.store.list("ctx","GPU")),2)
        self.assertTrue(all(r["status"]=="PENDING" for r in self.store.list("ctx","GPU")))
    def test_explicit_approval(self):
        token=self.store.propose_from_file("ctx","GPU",self.src)[0]
        self.assertTrue(self.store.review("ctx","GPU",token,"APPROVED"))
        self.assertFalse(self.store.review("ctx","GPU",token,"APPROVED"))
        self.assertEqual(self.store.list("ctx","GPU")[0]["status"],"APPROVED")
    def test_source_changed_blocks_review(self):
        token=self.store.propose_from_file("ctx","GPU",self.src)[0]
        self.src.write_text("GPUは並列計算に適さない。",encoding="utf8")
        self.assertFalse(self.store.review("ctx","GPU",token,"APPROVED"))
    def test_context_isolation(self):
        token=self.store.propose_from_file("ctx","GPU",self.src)[0]
        self.assertFalse(self.store.review("other","GPU",token,"APPROVED"))
    def test_concept_isolation(self):
        token=self.store.propose_from_file("ctx","GPU",self.src)[0]
        self.assertFalse(self.store.review("ctx","CPU",token,"APPROVED"))
    def test_invalid_utf8(self):
        self.src.write_bytes(b"\xff")
        with self.assertRaises(UnicodeDecodeError):scan_corpus(self.src,"GPU")
    def test_invalid_limit(self):
        with self.assertRaises(ValueError):scan_corpus(self.src,"GPU",limit=0)
    def test_only_exact_subject(self):
        self.assertEqual(scan_corpus(self.src,"量子力学"),[])
    def test_no_semantic_memory_mutation(self):
        before=self.src.read_bytes()
        self.store.propose_from_file("ctx","GPU",self.src)
        self.assertEqual(self.src.read_bytes(),before)
if __name__=="__main__":unittest.main()
