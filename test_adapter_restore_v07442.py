import tempfile
import unittest
from pathlib import Path
from verify_adapter_restore_v07442 import verify


class RestoreV07442Tests(unittest.TestCase):
    def test_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=verify(Path(tmp)/"missing.pt")
            self.assertEqual(r["status"],"FAILED")
            self.assertFalse(r["runtime_restore_verified"])

    def test_empty_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"empty.pt"
            p.touch()
            self.assertEqual(verify(p)["reason"],"CHECKPOINT_CORRUPT")


if __name__=="__main__":
    unittest.main()
