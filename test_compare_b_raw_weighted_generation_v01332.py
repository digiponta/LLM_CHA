import unittest
from compare_b_raw_weighted_generation_v01332 import repetition_ratio,summarize

class WeightedGenerationTests(unittest.TestCase):
    def test_repetition(self):
        self.assertEqual(repetition_ratio("abc"),0)
        self.assertGreater(repetition_ratio("abcabcabc"),0)
    def test_summary(self):
        row={"exact_text_match":False,"grounded_excerpt":True,
             "first_divergence_reencoded":0,"raw_generation":"abcabc",
             "generated_tokens":4}
        d=summarize([row])
        self.assertEqual(d["cases"],1)
        self.assertEqual(d["first_token_matches_reencoded"],0)
        self.assertEqual(d["grounded_excerpts"],1)
    def test_all_matched_prefix(self):
        row={"exact_text_match":True,"grounded_excerpt":True,
             "first_divergence_reencoded":None,"raw_generation":"回答",
             "generated_tokens":2}
        self.assertEqual(summarize([row])["first_token_matches_reencoded"],1)

if __name__=="__main__":unittest.main()
