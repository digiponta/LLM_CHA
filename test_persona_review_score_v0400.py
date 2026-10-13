import csv
import tempfile
import unittest
from pathlib import Path
from persona_review_v0378 import review_rows
from persona_review_score_v0400 import score,FIELDS

class PersonaScoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        root=Path(self.temp.name)
        self.corpus=root/"corpus.txt"
        self.corpus.write_text("私は数学を使って問題を解く。\n彼は電車によって移動する。",encoding="utf-8")
        self.csv=root/"review.csv"
        self.rows=review_rows(self.corpus)
        self.write()
    def tearDown(self):self.temp.cleanup()
    def write(self):
        with self.csv.open("w",encoding="utf-8-sig",newline="") as out:
            w=csv.DictWriter(out,fieldnames=[*FIELDS,"verdict","note"])
            w.writeheader();w.writerows(self.rows)
    def test_unreviewed_no_precision(self):
        x=score(self.corpus,self.csv)
        self.assertIsNone(x["precision_reviewed"])
        self.assertEqual(x["unreviewed"],2)
    def test_complete_reviews(self):
        self.rows[0]["verdict"]="CORRECT"
        self.rows[1]["verdict"]="INCORRECT"
        self.write()
        x=score(self.corpus,self.csv)
        self.assertEqual(x["precision_all_candidates"],.5)
        self.assertEqual(x["accepted_count"],1)
    def test_partial_no_full_precision(self):
        self.rows[0]["verdict"]="AMBIGUOUS"
        self.write()
        self.assertIsNone(score(self.corpus,self.csv)["precision_all_candidates"])
    def test_invalid_verdict_rejected(self):
        self.rows[0]["verdict"]="TRUE"
        self.write()
        with self.assertRaises(ValueError):score(self.corpus,self.csv)
    def test_role_edit_rejected(self):
        self.rows[0]["means"]="書籍"
        self.write()
        with self.assertRaises(ValueError):score(self.corpus,self.csv)
    def test_duplicate_id_rejected(self):
        self.rows[1]["id"]=self.rows[0]["id"]
        self.write()
        with self.assertRaises(ValueError):score(self.corpus,self.csv)
    def test_source_revision_rejected(self):
        self.corpus.write_text("私は機械を使って問題を解く。\n彼は電車によって移動する。",encoding="utf-8")
        with self.assertRaises(ValueError):score(self.corpus,self.csv)
    def test_runtime_unmodified(self):
        self.assertFalse(score(self.corpus,self.csv)["runtime_enabled"])
        self.assertEqual(score(self.corpus,self.csv)["truth_promotions"],0)
    def test_files_unchanged(self):
        old=(self.corpus.read_bytes(),self.csv.read_bytes())
        score(self.corpus,self.csv)
        self.assertEqual(old,(self.corpus.read_bytes(),self.csv.read_bytes()))
if __name__=="__main__":unittest.main()
