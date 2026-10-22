import tempfile
import unittest
from pathlib import Path
from synonym_lexicon_v0626 import SynonymLexicon
from synonym_candidate_review_v0627 import SynonymReview, extract_candidates

class ReviewTests(unittest.TestCase):
    def test_extract(self):
        self.assertIn(("ぬこ","猫"),extract_candidates("「ぬこ」は、猫の別名"))
    def test_related_word_is_not_synonym(self):
        self.assertEqual(extract_candidates("犬と猫は動物です"),[])
    def test_pending_approval(self):
        with tempfile.TemporaryDirectory() as d:
            lex=SynonymLexicon(Path(d)/"terms.jsonl")
            rev=SynonymReview(Path(d)/"candidates.jsonl",lex)
            r=rev.propose("クルマは自動車の別名")[0]
            self.assertEqual(r["state"],"PENDING")
            self.assertNotIn("クルマ",lex.expand("自動車"))
            rev.decide(r["id"],True)
            self.assertIn("クルマ",lex.expand("自動車"))
    def test_reject(self):
        with tempfile.TemporaryDirectory() as d:
            lex=SynonymLexicon(Path(d)/"terms.jsonl")
            rev=SynonymReview(Path(d)/"candidates.jsonl",lex)
            r=rev.propose("りんごはアップルの別名")[0]
            rev.decide(r["id"],False)
            self.assertNotIn("りんご",lex.expand("アップル"))
    def test_reload(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"candidates.jsonl"
            lex=SynonymLexicon(Path(d)/"terms.jsonl")
            SynonymReview(p,lex).propose("クルマは自動車の別名")
            self.assertEqual(len(SynonymReview(p,lex).pending()),1)
if __name__=="__main__":unittest.main()
