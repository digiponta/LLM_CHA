import tempfile
import unittest
from pathlib import Path
from audit_holdout_draft_v013588325 import audit, normalize
from generate_independent_holdout_draft_v013588325 import build

class AuditPathsRegressionTests(unittest.TestCase):
    def test_missing_path_is_reported_without_crashing(self):
        with tempfile.TemporaryDirectory() as d:
            missing = str(Path(d) / "absent.txt")
            result = audit(build(), [missing])
            self.assertEqual(result["sources_missing"], [missing])
            self.assertEqual(result["flag_counts"]["SOURCE_NOT_FOUND"], 1)
            self.assertFalse(result["independence_verified"])
    def test_whitespace_normalization(self):
        self.assertEqual(normalize("a  b\tc"), normalize("abc"))
    def test_existing_source_detects_overlap(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "source.txt"
            p.write_text("少し話せますか？\n", encoding="utf-8")
            result = audit(build(), [str(p)])
            self.assertEqual(result["flag_counts"]["EXACT_NORMALIZED_OVERLAP"], 1)
if __name__ == "__main__":
    unittest.main()
