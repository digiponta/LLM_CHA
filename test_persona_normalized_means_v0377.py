import tempfile
import unittest
from pathlib import Path
from persona_normalized_means_v0377 import normalized_rows,lookup

class NormalizedMeansTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/"corpus.txt"
        self.path.write_text("私は数学を使って問題を解く。\n彼は電車によって移動する。\n人は未知の装置によって未知を調べる。",encoding="utf-8")
    def tearDown(self):self.temp.cleanup()
    def test_all_markers_normalized(self):
        self.assertEqual(len(normalized_rows(self.path)),3)
    def test_means_lookup_quote_only_when_unlicensed(self):
        x=lookup(self.path,"数学は何をするもの？")
        self.assertEqual(x["mode"],"SOURCE_QUOTE")
        self.assertIn("私は数学を使って問題を解く",x["answer"])
    def test_subject_lookup(self):
        x=lookup(self.path,"私は何によって問題を解く？")
        self.assertEqual(x["means"],"数学")
        self.assertEqual(x["role"],"agent")
    def test_whitelisted_derivation(self):
        x=lookup(self.path,"電車は何をするもの？")
        self.assertEqual(x["mode"],"LICENSED_PARAPHRASE")
        self.assertEqual(x["answer"],"電車は彼を移動させる。")
    def test_unlicensed_causative_not_generated(self):
        x=lookup(self.path,"未知の装置は何をするもの？")
        self.assertEqual(x["mode"],"SOURCE_QUOTE")
        self.assertNotIn("調べさせる",x["answer"])
    def test_provenance(self):
        self.assertEqual(lookup(self.path,"数学は何をするもの？")["line"],1)
    def test_no_mutation(self):
        old=self.path.read_bytes()
        lookup(self.path,"数学は何をするもの？")
        self.assertEqual(old,self.path.read_bytes())
    def test_no_promotion(self):
        self.assertTrue(all(x["factual_truth"]=="NOT_ASSESSED" for x in normalized_rows(self.path)))
    def test_unknown_does_not_match(self):
        self.assertIsNone(lookup(self.path,"宇宙とは"))
    def test_runtime_wiring(self):
        source=Path("chat.py").read_text(encoding="utf-8")
        self.assertIn("normalized_means_lookup(",source)
        self.assertIn("truth_allows_direct_retrieval(normalized_truth.state)",source)
if __name__=="__main__":unittest.main()
