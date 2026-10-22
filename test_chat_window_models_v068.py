import tempfile
import unittest
from pathlib import Path
from chat_window_v061 import build_chat_command

class GuiModelSelectionTests(unittest.TestCase):
    def test_default_unchanged(self):
        with tempfile.TemporaryDirectory() as root:
            cmd, label = build_chat_command([], root)
            self.assertEqual(label, "chat.py default")
            self.assertNotIn("--model", cmd)

    def test_explicit_checkpoint_and_tokenizer(self):
        with tempfile.TemporaryDirectory() as root:
            base=Path(root)
            (base/"model").mkdir()
            (base/"model"/"custom.pt").touch()
            (base/"model"/"tokenizer.json").touch()
            cmd, label = build_chat_command(
                ["--model", "model/custom.pt", "--tokenizer", "model/tokenizer.json"], root)
            self.assertIn("--model", cmd)
            self.assertIn("--tokenizer", cmd)
            self.assertEqual(label, "custom.pt")

    def test_select_latest_experimental(self):
        with tempfile.TemporaryDirectory() as root:
            base=Path(root)
            (base/"model").mkdir()
            (base/"model"/"model-llm-cha-aozora-replay-v067-r2.pt").touch()
            (base/"model"/"tokenizer-v0.7-bpe.json").touch()
            cmd, label = build_chat_command(["--latest-experimental"], root)
            self.assertEqual(label, "model-llm-cha-aozora-replay-v067-r2.pt")
            self.assertIn("--tokenizer", cmd)

    def test_missing_experimental_fails(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(SystemExit):
                build_chat_command(["--latest-experimental"], root)

    def test_no_implicit_model_override(self):
        with tempfile.TemporaryDirectory() as root:
            base=Path(root)
            (base/"model").mkdir()
            (base/"model"/"model-llm-cha-aozora-v065.pt").touch()
            cmd, _ = build_chat_command([], root)
            self.assertNotIn("--model", cmd)

    def test_conflicting_flags_fails(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(SystemExit):
                build_chat_command(["--model", "x.pt", "--latest-experimental"], root)

if __name__ == "__main__":
    unittest.main()
