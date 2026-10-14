import unittest
from diagnose_japanese_foundation_qa_v042843 import build, propose


class DiagnosticsTests(unittest.TestCase):
    def test_retains_v42_definition(self):
        rows, _ = propose("量子力学とは微視的な現象を説明する理論。")
        self.assertEqual(rows[0]["type"], "definition")

    def test_conditional_expansion(self):
        rows, _ = propose("もし負荷が増えるなら、処理が遅くなる。")
        self.assertTrue(any(r["rule"] == "conditional-if" for r in rows))

    def test_negation_expansion(self):
        rows, _ = propose("この処理は実行できません。")
        self.assertTrue(any(r["type"] == "negation" for r in rows))

    def test_context_explicit_question(self):
        rows, _ = propose("ユーザー: 元気ですか？\nアシスタント: はい、元気です。")
        self.assertTrue(any(r["type"] == "context" for r in rows))

    def test_no_inferred_answer_for_why_question(self):
        rows, diagnostics = propose("なぜ空は青いのですか？")
        self.assertEqual(rows, [])
        self.assertEqual(diagnostics["unmatched_categories"]["question_without_answer"], 1)

    def test_unmatched_diagnostic(self):
        _, report = propose("何も一致しない文章。")
        self.assertEqual(report["unmatched_lines"], 1)

    def test_line_numbers_original(self):
        rows, _ = propose("# memo\n\n量子力学とは物理学の理論。")
        self.assertEqual(rows[0]["source_line"], 3)

    def test_no_auto_approval(self):
        result = build("量子力学とは物理学の理論。", "fixture")
        self.assertEqual(result["accepted"], 0)
        self.assertFalse(result["train_ready"])
        self.assertFalse(result["runtime_modified"])
        self.assertTrue(all(r["review_status"] == "pending" for r in result["candidates"]))

    def test_bad_limit(self):
        with self.assertRaises(ValueError):
            propose("text", 0)

if __name__ == "__main__":
    unittest.main()
