import unittest
from causal_question_normalization_v09765 import normalize_causal_question
from clipboard_causal_evidence_v09762 import retrieve

SOURCE = """スファレライト
脆さとカットの難しさ: 硬度が低いうえに6方向に完全な劈開があるため、ジュエリー加工やカットが非常に難しい宝石です。
圧倒的な輝き: 高い屈折率と分散度により、カラフルなファイアを楽しめます。
"""
class CausalParaphraseTests(unittest.TestCase):
    def test_variants(self):
        variants = ("なぜカットが難しい", "なぜカットが難しいの？",
                    "どうしてカットが難しいの？", "カットが難しい理由は？")
        for q in variants:
            with self.subTest(q=q):
                result = retrieve(normalize_causal_question(q), SOURCE, "スファレライト")
                self.assertIsNotNone(result)
                self.assertIn("劈開", result)
    def test_other_topic(self):
        self.assertIsNone(retrieve(normalize_causal_question("なぜカットが難しいの？"), SOURCE, "ダイヤモンド"))
    def test_fire(self):
        result=retrieve(normalize_causal_question("どうして虹色に輝くの？"), SOURCE, "スファレライト")
        self.assertIn("分散度",result)
    def test_not_answer_unrelated(self):
        self.assertIsNone(retrieve(normalize_causal_question("価格はいくら？"), SOURCE, "スファレライト"))

if __name__=="__main__":
    unittest.main()
