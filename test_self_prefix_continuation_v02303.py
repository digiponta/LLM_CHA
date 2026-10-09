import unittest
from diagnose_self_prefix_continuation_v02303 import split_prefix,analyze
class SelfPrefixTests(unittest.TestCase):
    def test_split(self):
        a,b=split_prefix([1,2,3,4],2)
        self.assertEqual(a,[1,2]);self.assertEqual(b,[3,4])
    def test_invalid_prefix(self):
        with self.assertRaises(ValueError):split_prefix([1],0)
    def test_relevant_suffix(self):
        r=analyze("宇宙探査","宇宙には、","探査機による観測が重要だ。","self_prefix")
        self.assertTrue(r["continuation_topic_lexical"])
    def test_irrelevant_suffix(self):
        r=analyze("歴史小説","歴史小説は、","宇宙に行こう。","self_prefix")
        self.assertFalse(r["continuation_topic_lexical"])
    def test_reference_prefix_is_not_success(self):
        r=analyze("カレー","カレーは、","そうですね。","reference_prefix")
        self.assertTrue(r["full_topic_exact"])
        self.assertFalse(r["continuation_topic_lexical"])
if __name__=="__main__":unittest.main()
