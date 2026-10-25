import unittest
from evaluate_emotion_quality_v09739 import quality,evaluate_report

class QualityTests(unittest.TestCase):
    def test_positive_wrong_response(self):
        self.assertEqual(quality("それは残念だったね。","POSITIVE")["verdict"],"FAIL")
        self.assertEqual(quality("良かったね。","POSITIVE")["verdict"],"PASS")
    def test_negative_sadness(self):
        self.assertEqual(quality("寂しいんだね。","NEGATED_SADNESS")["verdict"],"FAIL")
        self.assertEqual(quality("寂しくはないんだね。","NEGATED_SADNESS")["verdict"],"PASS")
    def test_mixed(self):
        self.assertEqual(quality("嬉しいけど悲しいんだね。","MIXED")["verdict"],"PASS")
        self.assertEqual(quality("それは残念だったね。","MIXED")["verdict"],"REVIEW")
    def test_persona(self):
        self.assertEqual(quality("長門有希。","IDENTITY")["verdict"],"PASS")
    def test_quality_report(self):
        r={"rows":[{"id":"x","input":"今日は楽しかった","emotion":"POSITIVE",
            "outputs":{a:{"text":"それは残念だったね。"} for a in ("plain","emotion","strategy","both")}}]}
        summary,detail=evaluate_report(r)
        self.assertEqual(len(detail),4)
        self.assertEqual(summary["by_arm"]["both"]["FAIL"],1)
        self.assertEqual(detail[0]["manual_verdict"],"")
if __name__=="__main__":unittest.main()
