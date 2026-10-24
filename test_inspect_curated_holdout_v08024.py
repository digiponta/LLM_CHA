import json
import tempfile
import unittest
from pathlib import Path
from inspect_curated_holdout_v08024 import inspect


class CuratedHoldoutInventoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "holdout.json"

    def write(self, value, encoding="utf-8"):
        self.path.write_text(json.dumps(value, ensure_ascii=False), encoding=encoding)

    def test_bom_empty_is_not_ready(self):
        self.write({"records": [], "independent_source_attested": False},
                   encoding="utf-8-sig")
        result = inspect(self.path)
        self.assertEqual(result["status"], "NOT_READY")
        self.assertIn("EMPTY_HOLDOUT", result["reasons"])
        self.assertFalse(result["written"])

    def test_missing_provenance_never_passes(self):
        self.write({"records": [{"id": "h-1", "evaluation_kind": "UNSEEN_FACT",
                                "question": "Question", "reference_answer": "Answer"}],
                    "independent_source_attested": True})
        result = inspect(self.path)
        self.assertEqual(result["status"], "NOT_READY")
        self.assertIn("MISSING_SOURCE_URL", result["issues"][0]["issues"])
        self.assertFalse(result["semantic_independence_verified"])

    def test_five_complete_records_are_only_gate_candidates(self):
        records = [{"id": f"human-{n}", "evaluation_kind": "UNSEEN_FACT",
                    "question": f"Question {n}", "reference_answer": f"Answer {n}",
                    "source_url": f"https://source.invalid/{n}",
                    "source_excerpt": f"Evidence {n}"} for n in range(5)]
        self.write({"records": records, "independent_source_attested": True})
        result = inspect(self.path)
        self.assertEqual(result["status"], "READY_FOR_FORMAL_GATE")
        self.assertFalse(result["semantic_independence_verified"])
        self.assertFalse(result["written"])


if __name__ == "__main__":
    unittest.main()
