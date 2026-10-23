"""CPU-only unit tests; no real GPU checkpoint required."""
import json
import tempfile
import unittest
from pathlib import Path
from diagnose_adapter_restore_v07441 import diagnose


class RestoreDiagnosticsTests(unittest.TestCase):
    def test_missing_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = diagnose(Path(tmp) / "missing.pt")
            self.assertEqual(r["reason"], "CHECKPOINT_NOT_FOUND")

    def test_empty_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "empty.pt"
            p.touch()
            self.assertEqual(diagnose(p)["reason"], "CHECKPOINT_CORRUPT")

    def test_malformed_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            p, s = Path(tmp) / "a.pt", Path(tmp) / "state.json"
            p.write_bytes(b"placeholder")
            s.write_text("{bad", encoding="utf-8")
            self.assertEqual(diagnose(p, state=s, load_payload=False)["reason"],
                             "SEMANTIC_STATE_MISMATCH")

    def test_metadata_only_does_not_claim_restoration(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "a.pt"
            p.write_bytes(b"placeholder")
            r = diagnose(p, load_payload=False)
            self.assertEqual(r["restore_status"], "PREFLIGHT_ONLY")
            self.assertFalse(r["runtime_restore_verified"])

    def test_output_is_non_destructive(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "a.pt"
            p.write_bytes(b"checkpoint")
            before = p.read_bytes()
            diagnose(p, load_payload=False)
            self.assertEqual(before, p.read_bytes())

    def test_valid_tensor_dictionary_when_torch_available(self):
        try:
            import torch
        except ImportError:
            self.skipTest("torch not installed")
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "a.pt"
            torch.save({"config": {"vocab_size": 10, "d_model": 4, "num_layers": 1, "hidden_dim": 8}, "model_state_dict": {"a.weight": torch.ones(2)}}, p)
            r = diagnose(p)
            self.assertEqual(r["restore_status"], "PREFLIGHT_OK")
            self.assertFalse(r["runtime_restore_verified"])

    def test_missing_model_keys(self):
        try:
            import torch
        except ImportError:
            self.skipTest("torch not installed")
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "a.pt"
            torch.save({"unrelated": 42}, p)
            self.assertEqual(diagnose(p)["reason"], "SCHEMA_MISMATCH")


if __name__ == "__main__":
    unittest.main()
