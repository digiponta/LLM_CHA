import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evaluate_aozora_models_v066 import validate_split, generate_samples, PROMPTS

class ModelComparisonTests(unittest.TestCase):
    def test_whole_work_holdout(self):
        train, held, chosen = validate_split([
            ("789", "猫1"), ("789", "猫2"), ("1567", "メロス")], "1567")
        self.assertEqual((train, held, chosen), (["猫1", "猫2"], ["メロス"], "1567"))

    def test_no_single_work_validation(self):
        with self.assertRaises(ValueError):
            validate_split([("789", "猫")], "789")

    def test_missing_work(self):
        with self.assertRaises(ValueError):
            validate_split([("789", "猫"), ("1567", "メロス")], "9999")

    def test_prompt_categories(self):
        self.assertGreaterEqual(len(PROMPTS), 4)
        self.assertIn("persona", {p["category"] for p in PROMPTS})
        self.assertIn("dialogue", {p["category"] for p in PROMPTS})
        self.assertIn("literature", {p["category"] for p in PROMPTS})

    def test_greedy_generation(self):
        class MockTokenizer:
            eos_id=3
            def encode(self, text): return [1, 2]
            def decode(self, ids): return "ANSWER"
        class MockModel:
            def generate(self, ids, **kwargs):
                self.kwargs=kwargs
                return ids+[4]
        model=MockModel()
        samples=generate_samples(model, MockTokenizer(), 8)
        self.assertEqual(len(samples), len(PROMPTS))
        self.assertEqual(samples[0]["answer"], "ANSWER")
        self.assertEqual(model.kwargs["temperature"], 0)

if __name__ == "__main__":
    unittest.main()
