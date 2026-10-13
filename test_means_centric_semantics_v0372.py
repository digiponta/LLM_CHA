import unittest
from means_centric_semantics_v0372 import transform,parse

class MeansCentricTests(unittest.TestCase):
    def test_train(self):
        self.assertEqual(transform("彼は電車によって移動する")["derived"],"電車は彼を移動させる。")
    def test_train_commas(self):
        self.assertEqual(transform("彼は、電車によって、移動する。")["derived"],"電車は彼を移動させる。")
    def test_tool(self):
        self.assertEqual(transform("人は道具によって作業する")["derived"],"道具は人に作業させる。")
    def test_medicine(self):
        self.assertEqual(transform("人は薬によって回復する")["derived"],"薬は人を回復させる。")
    def test_math(self):
        self.assertEqual(transform("私は数学によって問題を解く")["derived"],"数学は私に問題を解かせる。")
    def test_language(self):
        self.assertEqual(transform("人は言語によって意思を伝える")["derived"],"言語は人に意思を伝えさせる。")
    def test_semantics_retained(self):
        self.assertEqual(transform("彼は電車によって移動する")["semantic"]["relation"],"MEANS_OF")
    def test_not_factual_promotion(self):
        self.assertEqual(transform("彼は電車によって移動する")["factual_truth"],"NOT_ASSESSED")
    def test_unsupported_fails_closed(self):
        self.assertEqual(transform("彼は電車によって笑う")["status"],"UNSUPPORTED")
    def test_none(self):
        self.assertIsNone(parse(None))

if __name__=="__main__":unittest.main()
