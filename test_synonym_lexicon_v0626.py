import tempfile
import unittest
from pathlib import Path
from synonym_lexicon_v0626 import SynonymLexicon,learn_command,best_raw_mentions,learn_natural_statement

class SynonymTests(unittest.TestCase):
    def test_natural_alias(self):
        with tempfile.TemporaryDirectory() as d:
            l=SynonymLexicon(Path(d)/"terms.jsonl")
            result=learn_natural_statement("「ぬこ」も猫の別名",l)
            self.assertTrue(result["added"])
            self.assertIn("猫",l.expand("ぬこ"))
            self.assertIn("ぬこ",SynonymLexicon(Path(d)/"terms.jsonl").expand("猫"))
    def test_natural_statement_not_a_generic_request(self):
        with tempfile.TemporaryDirectory() as d:
            l=SynonymLexicon(Path(d)/"terms.jsonl")
            self.assertIsNone(learn_natural_statement("猫の特徴は",l))
    def test_cat(self):
        with tempfile.TemporaryDirectory() as d:
            l=SynonymLexicon(Path(d)/"terms.jsonl")
            self.assertIn("猫",l.expand("ネコ"))
            self.assertIn("ネコ",l.expand("猫"))
    def test_persistent_user_learning(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"terms.jsonl"
            l=SynonymLexicon(p)
            self.assertTrue(learn_command("/synonym-add 自動車 = クルマ",l)["added"])
            self.assertIn("自動車",SynonymLexicon(p).expand("クルマ"))
    def test_raw_evidence_alias(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"corpus.txt"
            p.write_text("猫は哺乳類の動物です。\n",encoding="utf-8")
            l=SynonymLexicon(Path(d)/"terms.jsonl")
            self.assertEqual(best_raw_mentions(p,l.expand("ネコ"))[0]["matched_alias"],"猫")
    def test_no_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            l=SynonymLexicon(Path(d)/"terms.jsonl")
            self.assertFalse(l.add("猫","ネコ"))
    def test_no_self_pair(self):
        with tempfile.TemporaryDirectory() as d:
            l=SynonymLexicon(Path(d)/"terms.jsonl")
            with self.assertRaises(ValueError):l.add("猫","猫")

if __name__=="__main__":unittest.main()
