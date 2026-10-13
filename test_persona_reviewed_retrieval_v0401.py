import csv
import tempfile
import unittest
from pathlib import Path
from persona_review_v0378 import review_rows
from persona_reviewed_retrieval_v0401 import reviewed_lookup

class ReviewedRetrievalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        root=Path(self.tmp.name)
        self.source=root/"corpus.txt"
        self.source.write_text("私は数学を使って問題を解く。\n彼は電車によって移動する。",encoding="utf-8")
        self.csv=root/"reviews.csv"
        self.rows=review_rows(self.source)
        self.write()
    def tearDown(self):self.tmp.cleanup()
    def write(self):
        with self.csv.open("w",encoding="utf-8-sig",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(self.rows[0]))
            w.writeheader();w.writerows(self.rows)
    def test_unreviewed_rejected(self):
        self.assertIsNone(reviewed_lookup(self.source,self.csv,"数学は何をするもの？"))
    def test_correct_quotes_original(self):
        self.rows[0]["verdict"]="CORRECT";self.write()
        got=reviewed_lookup(self.source,self.csv,"数学は何をするもの？")
        self.assertIn("私は数学を使って問題を解く",got["answer"])
        self.assertEqual(got["factual_truth"],"NOT_ASSESSED")
        self.assertEqual(got["mode"],"REVIEWED_SOURCE_QUOTE")
    def test_subject_reverse(self):
        self.rows[0]["verdict"]="CORRECT";self.write()
        self.assertEqual(reviewed_lookup(self.source,self.csv,"私は何によって問題を解く？")["means"],"数学")
    def test_ambiguous_excluded(self):
        self.rows[0]["verdict"]="AMBIGUOUS";self.write()
        self.assertIsNone(reviewed_lookup(self.source,self.csv,"数学は何をするもの？"))
    def test_incorrect_excluded(self):
        self.rows[0]["verdict"]="INCORRECT";self.write()
        self.assertIsNone(reviewed_lookup(self.source,self.csv,"数学は何をするもの？"))
    def test_missing_csv_fails(self):
        with self.assertRaises(OSError):reviewed_lookup(self.source,self.csv.with_name("missing.csv"),"数学は何をするもの？")
    def test_tampered_review_fails(self):
        self.rows[0]["verdict"]="CORRECT";self.rows[0]["means"]="物理";self.write()
        with self.assertRaises(ValueError):reviewed_lookup(self.source,self.csv,"数学は何をするもの？")
    def test_no_mutation(self):
        self.rows[0]["verdict"]="CORRECT";self.write()
        old=(self.source.read_bytes(),self.csv.read_bytes())
        reviewed_lookup(self.source,self.csv,"数学は何をするもの？")
        self.assertEqual(old,(self.source.read_bytes(),self.csv.read_bytes()))
    def test_runtime_opt_in_wiring(self):
        chat=Path("chat.py").read_text(encoding="utf-8")
        self.assertIn("LLM_CHA_REVIEWED_MEANS_ONLY",chat)
        self.assertIn("reviewed_lookup(",chat)
        self.assertIn("if reviewed_means_mode:",chat)
        self.assertIn("else:\n            # v0.3.7.5:",chat)
if __name__=="__main__":unittest.main()
