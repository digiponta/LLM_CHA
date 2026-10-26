import unittest
from clipboard_causal_evidence_v09762 import retrieve

SOURCE = """スファレライト
脆さとカットの難しさ: 硬度が低いうえに6方向に完全な劈開（へきかい）があるため、ジュエリー加工やカットが非常に難しい宝石です。
圧倒的な輝き: 高い屈折率と分散度により、カラフルなファイアを楽しめます。
カラッツSTORE
スファレライトはモース硬度が3.5-4と低く脆いためカットが難しいとされます。
"""
class Tests(unittest.TestCase):
    def test_google_result_duplicate_snippets(self):
        reply=retrieve("なぜカットが難しいの？",SOURCE,"スファレライト")
        self.assertIn("劈開",reply)
        self.assertIn("未検証",reply)
    def test_why_fire(self):
        self.assertIn("分散度",retrieve("なぜ虹色に輝くの？",SOURCE,"スファレライト"))
    def test_unrelated_topic(self):
        self.assertIsNone(retrieve("なぜカットが難しいの？",SOURCE,"ダイヤモンド"))
    def test_no_causal_support(self):
        self.assertIsNone(retrieve("なぜカットが難しいの？","スファレライト\n硬度は低い。","スファレライト"))
    def test_competing_labeled_explanations(self):
        s=SOURCE+"\n脆さとカットの難しさ: 別の理由により加工困難。"
        self.assertIsNone(retrieve("なぜカットが難しいの？",s,"スファレライト"))

if __name__=="__main__":
    unittest.main()
