import unittest
from evaluate_japanese_proposition_v0411 import synthetic_evidence
from article_proposition_alignment_v0412 import align
from compare_proposition_alignment_v0412 import compare

class GuardedDefinitionTests(unittest.TestCase):
    def extract(self,text):
        return align(synthetic_evidence(text))["proposition_count"]>0
    def test_guard_false_denial(self):self.assertFalse(self.extract("小説は文学ではないのである。"))
    def test_guard_negation(self):self.assertFalse(self.extract("小説は文学ではない。"))
    def test_guard_quotation(self):self.assertFalse(self.extract("「小説は文学である。」とする。"))
    def test_guard_question(self):self.assertFalse(self.extract("小説は文学である？"))
    def test_guard_hypothetical(self):self.assertFalse(self.extract("小説は文学であると仮定する。"))
    def test_toha(self):self.assertTrue(self.extract("小説とは文学の形式である。"))
    def test_meaning(self):self.assertTrue(self.extract("小説は創作文学を指す。"))
    def test_desu(self):self.assertTrue(self.extract("小説は文学の形式です。"))
    def test_one_of(self):self.assertTrue(self.extract("小説は文学の一つ。"))
    def test_reverse(self):self.assertTrue(self.extract("文学の一形式が小説である。"))
    def test_real_article(self):
        text="小説（しょうせつ、英: fiction（総称））は文学の形式の一つである。"
        r=align(synthetic_evidence(text))
        self.assertEqual(r["proposition_count"],1)
        self.assertEqual(r["propositions"][0]["evidence_text"],text)
    def test_metrics_and_safety(self):
        d=compare()
        self.assertEqual(d["v0411_cases"]["baseline"]["fp"],1)
        self.assertEqual(d["v0411_cases"]["baseline"]["fn"],5)
        self.assertEqual(d["v0411_cases"]["expanded"]["fp"],0)
        self.assertEqual(d["truth_promotions"],0)
        self.assertEqual(d["semantic_memory_writes"],0)
        self.assertFalse(d["training_enabled"])
if __name__=="__main__":unittest.main()
