import unittest
from compare_free_generation_v01330 import first_divergence,paraphrase,summarize

class FreeGenerationCompareTests(unittest.TestCase):
    def test_divergence(self):
        self.assertIsNone(first_divergence([1,2],[1,2]))
        self.assertEqual(first_divergence([1,2],[1,3]),1)
        self.assertEqual(first_divergence([1,2],[1]),1)
    def test_paraphrase(self):
        self.assertIn("時間",paraphrase("別の質問","時間"))
    def test_summary(self):
        r={"exact_text_match":False,"grounded_excerpt":True,
           "generated_tokens":12,"first_divergence_reencoded":0}
        out=summarize([r])
        self.assertEqual(out["grounded_excerpts"],1)
        self.assertEqual(out["first_token_matches_reencoded"],0)

if __name__=="__main__":unittest.main()
