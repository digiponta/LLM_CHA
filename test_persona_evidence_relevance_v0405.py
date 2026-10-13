import tempfile
import unittest
from pathlib import Path
from persona_evidence_relevance_v0405 import classify, inspect

class EvidenceRelevanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.corpus=Path(self.tmp.name)/"corpus.txt"
        self.corpus.write_text("数学は、文学の分類。\n文学とは、人間の表現のことである。\n小説について語る。",encoding="utf-8")
    def tearDown(self):self.tmp.cleanup()
    def test_secondary_mention(self):
        x=classify("数学は、文学の分類","文学")
        self.assertFalse(x["subject_match"])
        self.assertTrue(x["secondary_mention"])
        self.assertFalse(x["definition_pattern"])
    def test_definition_cue(self):
        x=classify("文学とは、人間の表現のことである","文学")
        self.assertTrue(x["subject_match"])
        self.assertTrue(x["definition_pattern"])
    def test_no_truth_certification(self):
        d=inspect(self.corpus,("文学",))
        self.assertFalse(d["truth_gate_modified"])
        self.assertEqual(d["human_relevance_reviewed"],0)
        self.assertFalse(d["concepts"][0]["definition_supported_by_human_review"])
    def test_ordering(self):
        x=inspect(self.corpus,("文学",))["concepts"][0]["top_candidates"]
        self.assertGreater(x[0]["heuristic_score"],x[1]["heuristic_score"])
    def test_missing(self):
        self.assertEqual(inspect(self.corpus,("GPU",))["concepts"][0]["top_candidates"],[])
    def test_no_corpus_mutation(self):
        before=self.corpus.read_bytes()
        inspect(self.corpus)
        self.assertEqual(before,self.corpus.read_bytes())
    def test_default_four(self):
        self.assertEqual([x["concept"] for x in inspect(self.corpus)["concepts"]],
                         ["数学","量子力学","文学","小説"])
if __name__=="__main__":unittest.main()
