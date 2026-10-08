"""CPU-only tests; no torch/checkpoint required."""
import tempfile
from pathlib import Path
import unittest
from character_profile_v010 import CharacterProfile, save_profile
from character_runtime_v010 import (
    available_profiles, character_command, select_profile, speaker
)

class CharacterRuntimeTests(unittest.TestCase):
    def test_select_and_off(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            save_profile(directory / "nagato.json",
                         CharacterProfile("nagato", "長門有希", "寡黙", "簡潔"))
            handled, active, _ = character_command("/character select nagato", directory, None)
            self.assertTrue(handled)
            self.assertEqual(speaker(active), "長門有希")
            handled, active, _ = character_command("/character off", directory, active)
            self.assertTrue(handled)
            self.assertIsNone(active)
            self.assertEqual(speaker(active), "AI")

    def test_invalid_selection_preserves_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            current = CharacterProfile("current", "Current")
            handled, active, message = character_command("/character select ../bad", temp, current)
            self.assertTrue(handled)
            self.assertIs(active, current)
            self.assertIn("failed", message)

    def test_no_semantic_files_written(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            save_profile(directory / "sample.json", CharacterProfile("sample", "Sample"))
            original = (directory / "sample.json").read_bytes()
            _, active, _ = character_command("/character select sample", directory, None)
            character_command("/character show", directory, active)
            character_command("/character off", directory, active)
            self.assertEqual((directory / "sample.json").read_bytes(), original)
            self.assertEqual(sorted(p.name for p in directory.iterdir()), ["sample.json"])

    def test_list_and_mismatched_id(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            save_profile(directory / "first.json", CharacterProfile("first", "First"))
            save_profile(directory / "wrong.json", CharacterProfile("second", "Second"))
            self.assertEqual(available_profiles(directory), ["first"])
            with self.assertRaises(ValueError):
                select_profile(directory, "wrong")

    def test_unknown_command_passes_through(self):
        handled, active, _ = character_command("/sleep", "characters", None)
        self.assertFalse(handled)
        self.assertIsNone(active)

    def test_default_label_and_multiline_normalization(self):
        self.assertEqual(speaker(None), "AI")
        self.assertEqual(speaker(CharacterProfile("a", "Long\nName")), "Long Name")

if __name__ == "__main__":
    unittest.main()
