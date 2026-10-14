import unittest
from expand_japanese_foundation_qa_v042842 import build, extract


class CoverageTests(unittest.TestCase):
    def test_definition(self):
        c = extract("量子力学とは微視的な現象を扱う理論。")
        self.assertEqual(c[0]["type"], "definition")
        self.assertFalse(c[0]["train_eligible"])

    def test_comparison(self):
        c = extract("CPUとGPUの違いは並列処理方式。")
        self.assertEqual(c[0]["type"], "comparison")

    def test_causal(self):
        self.assertEqual(extract("遅延の理由は通信距離が長い。")[0]["type"], "causal")

    def test_conditional(self):
        self.assertEqual(extract("負荷が増えた場合、処理が遅くなる。")[0]["type"], "conditional")

    def test_negation(self):
        self.assertEqual(extract("これは正解ではない。")[0]["type"], "negation")

    def test_explicit_context(self):
        c = extract("ユーザー: お元気ですか？\nアシスタント: はい、元気です。")
        self.assertEqual(c[0]["type"], "context")

    def test_dedup_and_fail_closed(self):
        text = "量子力学とは物理学の理論。\n量子力学とは物理学の理論。"
        r = build(text, "sample.txt")
        self.assertEqual(r["candidate_count"], 1)
        self.assertEqual(r["accepted"], 0)
        self.assertFalse(r["train_ready"])
        self.assertFalse(r["runtime_modified"])

    def test_limit(self):
        self.assertEqual(len(extract("Aとは説明です。\nBとは説明です。", 1)), 1)
        with self.assertRaises(ValueError):
            extract("Aとは説明です。", 0)


if __name__ == "__main__":
    unittest.main()
