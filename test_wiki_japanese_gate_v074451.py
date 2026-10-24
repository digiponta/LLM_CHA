import unittest
from wiki_fragment_gate_v074428 import coherent_scientific_evidence
from wiki_topic_memory_v074441 import _sentences

class JapaneseEvidenceRegressionTests(unittest.TestCase):
    def test_japanese_sentence_is_not_formula_orphan(self):
        sentence="量子ビットは量子情報科学および量子コンピュータにおいて情報を表現するための基本単位である"
        self.assertTrue(coherent_scientific_evidence(sentence))
    def test_short_math_orphan_is_rejected(self):
        self.assertFalse(coherent_scientific_evidence("alpha + beta = gamma"))
    def test_topic_evidence_split(self):
        article="量子ビットは量子情報科学および量子コンピュータにおいて情報を表現するための基本単位である。古典的なビットと異なり重ね合わせ状態をとることができる。"
        self.assertEqual(len(list(_sentences(article))),2)

if __name__=="__main__":
    unittest.main()
