import unittest
from analyze_initiation_distribution_v02272 import prompts, CASES

class AlignmentTests(unittest.TestCase):
    def test_single_format(self):
        s=prompts(CASES[0])["single"]
        self.assertTrue(s.startswith("人: 宇宙探査"))
        self.assertTrue(s.endswith("\nAI: "))

    def test_training_format(self):
        s=prompts(CASES[0])["training_format"]
        self.assertIn("人: 最近、SF小説に興味があります",s)
        self.assertIn("人: 宇宙探査です",s)
        self.assertTrue(s.endswith("人: その話を続けて\nAI: "))

    def test_holdout_case(self):
        self.assertEqual(CASES[-1]["topic"],"ミント")

if __name__=="__main__":
    unittest.main()
