import copy
import hashlib
import unittest

from audit_context_qa_v042844 import audit
from diagnose_japanese_foundation_qa_v042843 import build


def fixture(source):
    return build(source, "fixture")


class ContextAuditTests(unittest.TestCase):
    def test_good_explicit_pair_pending(self):
        source = "ユーザー: お元気ですか？\nアシスタント: はい、元気です。"
        r = audit(source, fixture(source))
        self.assertEqual(r["audited_context"], 1)
        self.assertEqual(r["accepted"], 0)
        self.assertEqual(r["audit_records"][0]["review_status"], "pending")
        self.assertEqual(r["audit_records"][0]["audit_status"], "review_priority_normal")

    def test_detect_topic_shift(self):
        source = "調子はどうですか？\nところで、別の話です。"
        r = audit(source, fixture(source))
        self.assertIn("possible_topic_shift", r["audit_records"][0]["flags"])

    def test_detect_source_tamper(self):
        source = "調子はどうですか？\n元気です。"
        d = fixture(source)
        d["candidates"][0]["answer"] = "変更した回答"
        r = audit(source, d)
        self.assertIn("answer_source_mismatch_or_nonadjacent", r["audit_records"][0]["flags"])

    def test_refuse_mismatched_source_hash(self):
        source = "調子はどうですか？\n元気です。"
        with self.assertRaises(ValueError):
            audit(source + "変更", fixture(source))

    def test_refuse_auto_approved_candidate(self):
        source = "調子はどうですか？\n元気です。"
        d = fixture(source)
        d["candidates"][0]["review_status"] = "approved"
        with self.assertRaises(ValueError):
            audit(source, d)

    def test_non_context_not_reviewed(self):
        source = "量子力学とは物理学の理論。"
        r = audit(source, fixture(source))
        self.assertEqual(r["audited_context"], 0)
        self.assertEqual(r["non_context_untouched"], 1)

    def test_line_number_with_comments(self):
        source = "# note\n\nユーザー: お元気ですか？\nアシスタント: はい、元気です。"
        r = audit(source, fixture(source))
        self.assertEqual(r["audit_records"][0]["source_line"], 3)

    def test_no_train_ready(self):
        source = "調子はどうですか？\n元気です。"
        r = audit(source, fixture(source))
        self.assertFalse(r["train_ready"])
        self.assertFalse(r["evaluation_ready"])
        self.assertFalse(r["runtime_modified"])

    def test_invalid_sample_limit(self):
        source = "調子はどうですか？\n元気です。"
        with self.assertRaises(ValueError):
            audit(source, fixture(source), -1)


if __name__ == "__main__":
    unittest.main()
