import unittest
from compare_literature_generation_v01356 import repetition, PROMPTS

class TestComparison(unittest.TestCase):
    def test_category_coverage(self):
        categories = {entry["category"] for entry in PROMPTS}
        self.assertIn("persona", categories)
        self.assertIn("literature", categories)
        self.assertIn("free_prose", categories)

    def test_unique_text(self):
        value = repetition("あいうえお")
        self.assertEqual(value["unique_bigram_fraction"], 1.0)

    def test_repeated_text(self):
        value = repetition("あいうあいうあいう")
        self.assertGreater(value["repeated_bigram_fraction"], 0.3)

    def test_empty_text(self):
        value = repetition("")
        self.assertEqual(value["repeated_bigram_fraction"], 0.0)

    def test_no_human_quality_claim(self):
        result = repetition("文章の生成")
        self.assertNotIn("human_quality_score", result)

if __name__ == "__main__":
    unittest.main()
