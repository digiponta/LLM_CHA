import tempfile
import unittest
from pathlib import Path
from audit_holdout_draft_v013588325 import audit, corpus_strings, normalize
from generate_independent_holdout_draft_v013588325 import build

class JsonlAuditTests(unittest.TestCase):
    def test_jsonl_nested_question_is_extracted(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "train.jsonl"
            p.write_text('{"dialogues":[{"question":"少し話せますか？","answer":"はい"}]}\n', encoding="utf-8")
            result = audit(build(), [str(p)])
            self.assertEqual(result["flag_counts"].get("EXACT_NORMALIZED_OVERLAP"), 1)
    def test_jsonl_utterances_array(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "dialogue.jsonl"
            p.write_text('{"utterances":[{"text":"今は話したくない"}]}\n', encoding="utf-8")
            self.assertIn("今は話したくない", corpus_strings(p))
            self.assertEqual(audit(build(), [str(p)])["flag_counts"].get("EXACT_NORMALIZED_OVERLAP"), 1)
    def test_whitespace_is_normalized(self):
        self.assertEqual(normalize("少し 話せますか？"), normalize("少し話せますか？"))
    def test_invalid_jsonl_is_rejected_not_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.jsonl"
            p.write_text('{"invalid"\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "INVALID_JSONL"):
                audit(build(), [str(p)])
if __name__ == "__main__":
    unittest.main()
