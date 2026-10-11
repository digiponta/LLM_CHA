import json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from semantic_coverage_admission_v023364 import inspect_coverage,render_coverage

class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        p=Path(self.tmp.name)
        self.atomic=p/"atomic.jsonl";self.subject=p/"subject.jsonl"
        self.typed=p/"typed.jsonl";self.unified=p/"unified.jsonl"
        self.corpus=p/"corpus.jsonl";self.manifest=p/"missing.json"
        def write(path,items):
            path.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in items),encoding="utf8")
        write(self.atomic,[])
        write(self.subject,[])
        write(self.typed,[])
        write(self.unified,[{"concept":"量子力学","assistant":"raw corpus mirror"}])
        write(self.corpus,[{"subject":"量子力学","content":"raw knowledge"}])
        self.result=NS(state="RAW_CORPUS_ONLY",truth_state="UNVERIFIED",action="BLOCK",
                       answer="",provenance=NS(source="raw-corpus",evidence="",origin=""))
        self.semantic=NS(resolve=lambda query:self.result)
    def inspect(self):
        return inspect_coverage("量子力学",self.atomic,self.subject,self.typed,
                                self.unified,self.corpus,self.semantic,self.manifest)
    def test_corpus_only_not_zero_coverage(self):
        r=self.inspect()
        self.assertEqual(r["atomic"],0)
        self.assertEqual(r["corpus_records"],1)
        self.assertEqual(r["unified_concepts"],1)
    def test_unverified_rejected(self):
        r=self.inspect()
        self.assertFalse(r["evidence_admissible"])
        self.assertEqual(r["admission_reason"],"truth_not_true")
    def test_unified_presence_not_truth(self):
        self.assertIn("Evidence=BLOCK",render_coverage(self.inspect()))
    def test_no_manifest(self):
        self.assertFalse(self.inspect()["manifest_present"])
    def test_missing_corpus(self):
        self.corpus.unlink()
        self.assertEqual(self.inspect()["corpus_records"],0)

if __name__=="__main__":unittest.main()
