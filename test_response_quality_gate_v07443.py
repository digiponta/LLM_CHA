import unittest
from response_quality_gate_v07443 import assess_response

class ResponseQualityGateTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(assess_response("今日は静かな一日だった。").action,"ACCEPT")
    def test_gap_requires_review(self):
        self.assertEqual(assess_response("そう。少し話そう。",persona_gap=True).action,"REVIEW")
    def test_empty_gap(self):
        self.assertEqual(assess_response("",persona_gap=True).action,"RETRY")
    def test_repetition(self):
        self.assertEqual(assess_response("同じ文章を繰り返す。"*3).action,"RETRY")
    def test_invalid_unicode_replacement(self):
        self.assertEqual(assess_response("表示が\ufffd壊れている").action,"RETRY")
    def test_evidence_quarantine(self):
        self.assertEqual(assess_response("未確認の仮説だ。",route="GENERATED_EVIDENCE",truth_state="UNVERIFIED").action,"HOLD")
    def test_trusted_preserved(self):
        self.assertEqual(assess_response("同じ文章を繰り返す。"*3,route="TRUSTED_RETRIEVAL",persona_gap=True).action,"ACCEPT")
    def test_normal_question(self):
        self.assertEqual(assess_response("どうしたの？").action,"ACCEPT")

if __name__=="__main__":
    unittest.main()
