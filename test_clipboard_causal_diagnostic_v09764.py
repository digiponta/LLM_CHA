import unittest
from clipboard_causal_diagnostic_v09764 import diagnose
from clipboard_causal_evidence_v09762 import retrieve

SOURCE = """スファレライト
脆さとカットの難しさ: 硬度が低いうえに6方向に完全な劈開（へきかい＝特定の方向に割れやすい性質）があるため、ジュエリー加工やカットが非常に難しい宝石です。そのため、ルースとして流通しています。
スファレライトはモース硬度が低く脆いためカットが難しいとされます。
"""
class DiagnosticTests(unittest.TestCase):
    def test_exact_reported_question(self):
        q = "なぜカットが難しいの？"
        result = diagnose(q,SOURCE,"スファレライト")
        self.assertEqual(result["labeled_count"],1)
        self.assertIn("劈開", retrieve(q,SOURCE,"スファレライト"))

    def test_topic_missing(self):
        self.assertEqual(diagnose("なぜカットが難しいの？",SOURCE,None)["reason"],"TOPIC_MISSING")

    def test_no_source(self):
        self.assertEqual(diagnose("なぜカットが難しいの？","","スファレライト")["reason"],"TOPIC_NOT_IN_SOURCE_HEAD")

if __name__ == "__main__":
    unittest.main()
