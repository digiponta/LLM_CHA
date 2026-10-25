import unittest
from explicit_topic_corpus_v0941 import corpus_mentions,augment_explicit_answer
class ExplicitCorpusTests(unittest.TestCase):
    def setUp(self):
        self.corpus="数学は、文学の分類。\n文学とは、言語による表現。\n量子力学は複雑だ。"
    def test_math_statement_preserved(self):
        r=augment_explicit_answer("数学","Wikipediaによると、数学は学問。",self.corpus)
        self.assertIn("数学は、文学の分類。",r["answer"])
        self.assertIn("Wikipediaによると",r["answer"])
        self.assertFalse(r["auto_promote"])
    def test_no_match(self):
        r=augment_explicit_answer("古生物学","Wikipediaの説明",self.corpus)
        self.assertEqual(r["answer"],"Wikipediaの説明")
    def test_exact_subject_preferred(self):
        matches=corpus_mentions("数学","数学による応用研究を進める。\n数学は、文学の分類。")
        self.assertEqual(matches[0],"数学は、文学の分類。")
if __name__=="__main__":unittest.main()
