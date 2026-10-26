import unittest
from analyze_semantic_divergence_v0100 import first_difference

class DivergenceTests(unittest.TestCase):
    def test_identical(self):
        self.assertIsNone(first_difference([1,2,3],[1,2,3]))
    def test_first_token(self):
        self.assertEqual(first_difference([1,2],[4,2]),0)
    def test_late_token(self):
        self.assertEqual(first_difference([1,2,3],[1,2,4]),2)
    def test_early_stop(self):
        self.assertEqual(first_difference([1,2,3],[1,2]),2)
    def test_extra_generated_token(self):
        self.assertEqual(first_difference([1,2],[1,2,3]),2)
if __name__=="__main__":unittest.main()
