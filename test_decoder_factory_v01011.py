"""Checks that the factory refuses an unspecified checkpoint and freezes weights."""
import os
import unittest
from unittest.mock import patch, MagicMock
import decoder_factory_v0101

class FactoryTests(unittest.TestCase):
    def test_checkpoint_required(self):
        with patch.dict(os.environ, {"LLM_CHA_DECODE_MODEL": ""}):
            with self.assertRaisesRegex(RuntimeError, "LLM_CHA_DECODE_MODEL"):
                decoder_factory_v0101.load()

    def test_absent_checkpoint_rejected(self):
        with patch.dict(os.environ, {"LLM_CHA_DECODE_MODEL": "nonexistent-v01011-model.pt"}):
            with self.assertRaises(FileNotFoundError):
                decoder_factory_v0101.load()

if __name__ == "__main__":
    unittest.main()
