import unittest
from compare_first_token_learning_v01328 import compare

class FirstTokenLearningTests(unittest.TestCase):
    def test_improvement(self):
        before={"first_token_id":12,"first_rank":100,"first_probability":0.001,"first_nll":7.0,"answer_nll":4.0}
        after={"first_token_id":12,"first_rank":10,"first_probability":0.01,"first_nll":4.7,"answer_nll":2.0}
        d=compare(before,after)
        self.assertEqual(d["rank_improvement"],90)
        self.assertAlmostEqual(d["probability_ratio"],10)
        self.assertAlmostEqual(d["answer_nll_improvement"],2)
    def test_target_mismatch(self):
        a={"first_token_id":1};b={"first_token_id":2}
        with self.assertRaises(ValueError):compare(a,b)
    def test_regression(self):
        a={"first_token_id":1,"first_rank":2,"first_probability":.3,"first_nll":1,"answer_nll":2}
        b={"first_token_id":1,"first_rank":3,"first_probability":.2,"first_nll":2,"answer_nll":3}
        self.assertLess(compare(a,b)["rank_improvement"],0)

if __name__=="__main__":unittest.main()
