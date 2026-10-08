"""CPU-only standard-library tests for LLM_CHA character profiles.

Run: python -m unittest -v test_character_profile_v010.py
"""
import json
from pathlib import Path
import tempfile
import unittest

from character_profile_v010 import CharacterProfile, describe_profile, load_profile, save_profile


class CharacterProfileTests(unittest.TestCase):
    def test_round_trip_japanese(self):
        profile = CharacterProfile("nagato", "長門有希", "寡黙", "簡潔に答える")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profiles" / "nagato.json"
            save_profile(path, profile)
            self.assertEqual(load_profile(path), profile)
            self.assertIn("長門有希", path.read_text(encoding="utf-8"))
            self.assertIn("Speaking style:", describe_profile(profile))

    def test_invalid_id(self):
        with self.assertRaises(ValueError):
            CharacterProfile("../escape", "Name")

    def test_empty_name(self):
        with self.assertRaises(ValueError):
            CharacterProfile("test", "   ")

    def test_oversized_persona(self):
        with self.assertRaises(ValueError):
            CharacterProfile("test", "Name", "x" * 2001)

    def test_unknown_fields_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            path.write_text(json.dumps({
                "profile_id": "test",
                "display_name": "Name",
                "persona": "",
                "speaking_style": "",
                "extra": "unsupported",
            }), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_profile(path)

    def test_no_training_or_chat_dependency(self):
        profile = CharacterProfile("test", "Name")
        self.assertEqual(profile.persona, "")
        self.assertEqual(profile.speaking_style, "")


if __name__ == "__main__":
    unittest.main()
