import tempfile
import unittest
from pathlib import Path
from persona_means_audit_v0376 import extract,audit

class PersonaMeansAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/"data.txt"
        self.path.write_text(
            "彼は電車によって移動する。\n"
            "私は数学を使って問題を解く。\n"
            "彼は言語を通じて意思を伝える。\n"
            "人は未知の装置によって未知の現象を調べる。\n"
            "彼は何もしない。",encoding="utf-8")
    def tearDown(self):self.temp.cleanup()
    def test_markers(self):
        self.assertEqual(audit(self.path)["by_marker"],{"によって":2,"を使って":1,"を通じて":1})
    def test_extract_count(self):
        self.assertEqual(len(extract(self.path)),4)
    def test_causative_only_licensed(self):
        result=audit(self.path)
        self.assertEqual(result["causative_derivable"],1)
        self.assertEqual(result["unrendered_candidates"],3)
    def test_source_coordinates(self):
        self.assertEqual([x["line"] for x in extract(self.path)],[1,2,3,4])
    def test_original_source_kept(self):
        self.assertEqual(extract(self.path)[0]["original"],"彼は電車によって移動する")
    def test_truth_unassessed(self):
        self.assertTrue(all(x["factual_truth"]=="NOT_ASSESSED" for x in extract(self.path)))
    def test_not_promoted(self):
        self.assertEqual(audit(self.path)["factual_promotions"],0)
    def test_no_corpus_mutation(self):
        before=self.path.read_bytes();audit(self.path);self.assertEqual(self.path.read_bytes(),before)
    def test_derived_japanese(self):
        self.assertEqual(extract(self.path)[0]["derived"],"電車は彼を移動させる。")
    def test_unsupported_no_derived(self):
        self.assertIsNone(extract(self.path)[3]["derived"])
if __name__=="__main__":unittest.main()
