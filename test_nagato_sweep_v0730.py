import unittest
from sweep_nagato_generation_v0730 import BUDGETS,common_prefix,sweep

class NagatoSweepTests(unittest.TestCase):
    def setUp(self):
        self.rows=[{"id":"a","source_id":"data-nagato.txt:line=1",
                    "question":"Q","answer":"abcdef"}]
    def test_budgets(self):
        self.assertEqual(BUDGETS,(32,64,128,256))
    def test_prefix(self):
        self.assertEqual(common_prefix([1,2,3],[1,2,4]),2)
    def test_length_fit_and_exact(self):
        tokenizer=type("T",(),{"encode":staticmethod(lambda text:list(text))})()
        result=sweep(self.rows,tokenizer,lambda q,n:"abcdef" if n>=6 else "abc",(3,6))
        self.assertEqual(result["sweep"][0]["exact"],0)
        self.assertEqual(result["sweep"][0]["fit_count"],0)
        self.assertEqual(result["sweep"][1]["exact"],1)
        self.assertEqual(result["sweep"][1]["fit_count"],1)
    def test_empty_rejected(self):
        with self.assertRaises(ValueError):sweep([],None,None)
if __name__=="__main__":unittest.main()
