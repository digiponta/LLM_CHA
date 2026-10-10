import unittest
from evaluate_copy_ood_robustness_v023317 import PROBES,validate_groups,summarize

class OODTests(unittest.TestCase):
    def test_groups(self):
        self.assertEqual(set(PROBES),{"unseen_vocabulary","unseen_syntax","longer_sentences",
                "multiple_sentences","symbols_numbers","original_benchmark"})
        self.assertTrue(validate_groups(PROBES))
    def test_duplicate_detection(self):
        with self.assertRaises(ValueError):
            validate_groups({"x":["same"],"y":["same"]})
    def test_empty_detection(self):
        with self.assertRaises(ValueError):
            validate_groups({"empty":[]})
    def test_summary_skips(self):
        rows=[{"skipped":False,"exact_text":True,"exact_tokens":True,"tokenizer_roundtrip":True},
              {"skipped":False,"exact_text":False,"exact_tokens":False,"tokenizer_roundtrip":True},
              {"skipped":True}]
        stats=summarize(rows)
        self.assertEqual(stats["evaluated"],2)
        self.assertEqual(stats["skipped"],1)
        self.assertEqual(stats["exact_text"],1)
        self.assertEqual(stats["exact_accuracy"],0.5)
if __name__=="__main__":unittest.main()
