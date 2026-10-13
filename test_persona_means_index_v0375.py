import tempfile
import unittest
from pathlib import Path
from persona_means_index_v0375 import build_index,lookup,query_focus

class MeansIndexTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/"persona.txt"
        self.path.write_text("私は数学によって問題を解く。\n彼は電車によって移動する。\n数学は美しい。",encoding="utf-8")
    def tearDown(self):
        self.tmp.cleanup()
    def test_index_roles(self):
        self.assertEqual(len(build_index(self.path)),2)
    def test_means_forward(self):
        row=lookup(self.path,"数学は何をするもの？")
        self.assertEqual(row["answer"],"数学は私に問題を解かせる。")
    def test_agent_reverse(self):
        row=lookup(self.path,"私は何によって問題を解く？")
        self.assertEqual(row["answer"],"私は数学によって問題を解く")
    def test_train_case(self):
        self.assertEqual(lookup(self.path,"電車は何をする？")["answer"],"電車は彼を移動させる。")
    def test_no_match(self):
        self.assertIsNone(lookup(self.path,"宇宙とは"))
    def test_no_invented_relation(self):
        self.assertIsNone(lookup(self.path,"美しいものは何をする？"))
    def test_provenance(self):
        self.assertEqual(lookup(self.path,"数学は何をするもの？")["line"],1)
    def test_truth_not_promoted(self):
        self.assertEqual(lookup(self.path,"数学は何をするもの？")["factual_truth"],"NOT_ASSESSED")
    def test_source_not_mutated(self):
        old=self.path.read_bytes()
        lookup(self.path,"電車は何をする？")
        self.assertEqual(old,self.path.read_bytes())
    def test_runtime_route(self):
        s=Path("chat.py").read_text(encoding="utf-8")
        self.assertIn("persona_means_lookup(",s)
        self.assertIn("truth_allows_direct_retrieval(means_truth.state)",s)
        self.assertIn("persona> {means_result",s)
if __name__=="__main__":unittest.main()
