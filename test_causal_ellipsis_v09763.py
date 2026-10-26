import unittest
from clipboard_causal_evidence_v09762 import retrieve

SOURCE = """スファレライト
脆さとカットの難しさ: 硬度が低いうえに6方向に完全な劈開（へきかい＝特定の方向に割れやすい性質）があるため、ジュエリー加工やカットが非常に難しい宝石です。そのため、リングやブレスレットよりも、コレクター向けのルース（裸石）として流通することが多いです。
スファレライトはモース硬度が3.5-4と低く脆いためカットが難しいとされます。
圧倒的な輝き: 高い屈折率と分散度により、カラフルなファイアを楽しめます。
"""

class FollowupSubjectTests(unittest.TestCase):
    def test_why_cut_question_ending_no(self):
        result = retrieve("なぜカットが難しいの？", SOURCE, "スファレライト")
        self.assertIsNotNone(result)
        self.assertIn("劈開", result)
        self.assertIn("未検証", result)

    def test_unrelated_explicit_subject_rejected(self):
        self.assertIsNone(retrieve("ダイヤモンドのカットが難しい理由は？", SOURCE, "スファレライト"))

    def test_why_fire(self):
        self.assertIn("分散度", retrieve("なぜ虹色に輝くの？",SOURCE,"スファレライト"))

    def test_no_context(self):
        self.assertIsNone(retrieve("なぜカットが難しいの？",SOURCE,None))

if __name__ == "__main__":
    unittest.main()
