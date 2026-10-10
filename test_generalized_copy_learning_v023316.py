import unittest
from generalized_copy_learning_v023316 import corpus,split_corpus,rows

class GeneralizedCopyTests(unittest.TestCase):
    def test_corpus_size_and_uniqueness(self):
        all_cases=corpus()
        self.assertEqual(len(all_cases),8*8*8*4)
        self.assertEqual(len(all_cases),len(set(all_cases)))
    def test_disjoint_splits(self):
        a,b,c=split_corpus()
        self.assertEqual((len(a),len(b),len(c)),(480,80,80))
        self.assertFalse(set(a)&set(b))
        self.assertFalse(set(a)&set(c))
        self.assertFalse(set(b)&set(c))
    def test_split_determinism(self):
        self.assertEqual(split_corpus(42),split_corpus(42))
        self.assertNotEqual(split_corpus(42)[0],split_corpus(43)[0])
    def test_rows_preserve_copy_target(self):
        a,_,_=split_corpus(42,3,2,2)
        self.assertEqual([r["answer"] for r in rows(a)],a)
    def test_invalid_splits(self):
        with self.assertRaises(ValueError):split_corpus(42,2048,80,80)

if __name__=="__main__":unittest.main()
