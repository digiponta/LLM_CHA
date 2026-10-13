import tempfile
import unittest
from pathlib import Path
from persona_review_v0378 import review_rows,evaluate,candidate_id,VERDICTS

class PersonaReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.source=Path(self.temp.name)/"corpus.txt"
        self.source.write_text("私は数学を使って問題を解く。\n彼は電車によって移動する。",encoding="utf-8")
    def tearDown(self):self.temp.cleanup()
    def test_candidate_count(self):self.assertEqual(len(review_rows(self.source)),2)
    def test_all_unreviewed(self):self.assertTrue(all(x["verdict"]=="UNREVIEWED" for x in review_rows(self.source)))
    def test_original_preserved(self):self.assertEqual(review_rows(self.source)[0]["original"],"私は数学を使って問題を解く")
    def test_source_coordinates(self):self.assertEqual([x["line"] for x in review_rows(self.source)],[1,2])
    def test_stable_id(self):self.assertEqual(review_rows(self.source)[0]["id"],review_rows(self.source)[0]["id"])
    def test_role_probes(self):self.assertEqual(evaluate(self.source)["probes"],4)
    def test_hits(self):self.assertEqual(evaluate(self.source)["source_hit_count"],4)
    def test_precision_unset(self):self.assertIsNone(evaluate(self.source)["precision"])
    def test_no_mutation(self):
        original=self.source.read_bytes();evaluate(self.source);self.assertEqual(original,self.source.read_bytes())
    def test_verdict_schema(self):self.assertEqual(VERDICTS,("CORRECT","AMBIGUOUS","INCORRECT"))
if __name__=="__main__":unittest.main()
