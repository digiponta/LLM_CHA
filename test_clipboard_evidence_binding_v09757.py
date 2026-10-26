import unittest

from clipboard_evidence_binding_v09757 import ClipboardEvidenceSession


class ClipboardEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.s = ClipboardEvidenceSession()
        self.s.ingest(
            "スファレライトは化学組成が硫化亜鉛（ZnS）の鉱物である。\n"
            "無関係なページにもZnSと書かれている。",
            subject="スファレライト",
        )

    def test_direct(self):
        a = self.s.answer("スファレライトの成分は")
        self.assertEqual(a.value, "硫化亜鉛（ZnS）")
        self.assertEqual(a.truth_state, "EXTERNAL_UNVERIFIED")

    def test_followup(self):
        self.assertIn("ZnS", self.s.answer("化学組成を知りたい").render())

    def test_unrelated_query(self):
        self.assertIsNone(self.s.answer("産地を知りたい"))

    def test_other_subject(self):
        self.assertIsNone(self.s.answer("化学組成を知りたい", resolved_subject="ダイヤモンド"))

    def test_no_unrelated_fact_leak(self):
        s = ClipboardEvidenceSession()
        s.ingest("別の鉱物の化学組成が硫化亜鉛（ZnS）。", subject="スファレライト")
        self.assertIsNone(s.answer("成分は"))

    def test_reset(self):
        self.s.clear()
        self.assertIsNone(self.s.answer("化学組成を知りたい"))

    def test_size_guard(self):
        s = ClipboardEvidenceSession(max_chars=10)
        s.ingest("スファレライトは化学組成が硫化亜鉛（ZnS）の鉱物である。", subject="スファレライト")
        self.assertIsNone(s.answer("化学組成"))

    def test_no_knowledge_promotion(self):
        a = self.s.answer("化学組成")
        self.assertEqual(a.source, "clipboard")
        self.assertFalse(hasattr(self.s, "promote"))
        self.assertFalse(hasattr(self.s, "sleep"))


if __name__ == "__main__":
    unittest.main()
