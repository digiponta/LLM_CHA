import unittest
from clipboard_causal_evidence_v09760 import retrieve

TEXT = """スファレライト
圧倒的な輝き: 高い屈折率と分散度により、強い光沢とカラフルなファイアを楽しめます。
脆さとカットの難しさ: 硬度が低いうえに6方向に完全な劈開があるため、ジュエリー加工やカットが非常に難しい宝石です。
"""

class CausalEvidenceTests(unittest.TestCase):
    def test_cutting(self):
        self.assertIn("劈開", retrieve("なぜカットが難しいの？", TEXT, "スファレライト"))

    def test_fire(self):
        self.assertIn("分散度", retrieve("なぜ虹色に輝くの？", TEXT, "スファレライト"))

    def test_missing_cause(self):
        self.assertIsNone(retrieve("なぜカットが難しいの？", "スファレライト\nカットが難しい。", "スファレライト"))

    def test_unrelated(self):
        self.assertIsNone(retrieve("値段はいくら？", TEXT, "スファレライト"))

    def test_no_topic(self):
        self.assertIsNone(retrieve("なぜカットが難しいの？", TEXT))

    def test_wrong_subject(self):
        self.assertIsNone(retrieve("ダイヤモンドのカットが難しい理由は？", TEXT, "スファレライト"))

    def test_ambiguity(self):
        dup = TEXT + "\nカットが難しいのは産出が少ないため。"
        self.assertIsNone(retrieve("なぜカットが難しいの？",dup,"スファレライト"))


if __name__ == "__main__":
    unittest.main()
