import tempfile,unittest
from pathlib import Path
from safe_semantic_bootstrap_v013588274 import assess,initialize

class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();d=Path(self.tmp.name)
        self.paths={k:str(d/(k+".jsonl")) for k in ("atomic","subject_index","typed_index","unified","truth")}
        Path(self.paths["unified"]).write_text('{"concept":"先行知識","assistant":"既存の知識"}\n',encoding="utf-8")
    def tearDown(self):self.tmp.cleanup()
    def test_ready(self):
        x=assess(self.paths)
        self.assertEqual(x["status"],"BOOTSTRAP_READY")
        self.assertEqual(len(x["to_initialize"]),4)
    def test_dry_run_unchanged(self):
        original=Path(self.paths["unified"]).read_bytes()
        x=initialize(self.paths)
        self.assertFalse(x["changed"])
        self.assertFalse(Path(self.paths["atomic"]).exists())
        self.assertEqual(Path(self.paths["unified"]).read_bytes(),original)
    def test_commit_preserves_unified(self):
        before=Path(self.paths["unified"]).read_bytes()
        x=initialize(self.paths,commit=True)
        self.assertEqual(x["status"],"BOOTSTRAP_COMPLETE")
        self.assertEqual(len(x["created"]),4)
        self.assertEqual(Path(self.paths["unified"]).read_bytes(),before)
        self.assertEqual(Path(x["backup"]).read_bytes(),before)
        self.assertEqual(assess(self.paths)["to_initialize"],[])
    def test_unified_missing_blocks(self):
        Path(self.paths["unified"]).unlink()
        self.assertEqual(assess(self.paths)["status"],"BLOCKED_UNIFIED_NOT_VALID")
    def test_unified_invalid_blocks(self):
        Path(self.paths["unified"]).write_text("broken",encoding="utf-8")
        self.assertEqual(assess(self.paths)["status"],"BLOCKED_UNIFIED_NOT_VALID")
    def test_missing_directory_no_created_stores(self):
        self.paths["typed_index"]=str(Path(self.tmp.name)/"absent"/"typed.jsonl")
        with self.assertRaises(ValueError):
            initialize(self.paths,commit=True)
        self.assertFalse(Path(self.paths["atomic"]).exists())
    def test_overlap_blocks(self):
        self.paths["atomic"]=self.paths["unified"]
        self.assertEqual(assess(self.paths)["status"],"BLOCKED_OVERLAPPING_PATHS")
if __name__=="__main__":unittest.main()
