import unittest
from response_quality_gate_v0633 import response_quality, gate_quality_report

CASES=[
 {"id":"identity","group":"persona"},
 {"id":"greeting","group":"persona"},
 {"id":"cat","group":"known"},
 {"id":"new_training_example","group":"new","acceptable_answers":["検証専用の合言葉です。"]},
]
class ResponseQualityTests(unittest.TestCase):
    def test_reported_greeting_regression(self):
        self.assertTrue(response_quality("こんばんは。お疲れ様",CASES[1])["pass"])
        self.assertFalse(response_quality("こんばんは。お疲れ行きつけの患者役。",CASES[1])["pass"])
    def test_reported_cat_regression(self):
        self.assertTrue(response_quality("ネコ",CASES[2])["pass"])
        self.assertFalse(response_quality("ネコ領域に属する。",CASES[2])["pass"])
    def test_identity_preserved(self):
        self.assertTrue(response_quality("長門有希。",CASES[0])["pass"])
    def test_new_learning(self):
        self.assertTrue(response_quality("検証専用の合言葉です。",CASES[3])["pass"])
    def test_report_from_user_example_fails(self):
        before={"identity":"あなた => 長門有希","greeting":"こんばんは。お疲れ様",
                "cat":"ネコ","new_training_example":"学習済み出される。"}
        after={"identity":"長門有希。","greeting":"こんばんは。お疲れ行きつけの患者役。",
               "cat":"ネコ領域に属する。","new_training_example":"検証専用の合言葉です。"}
        result=gate_quality_report({"answers":{"before":before,"after":after}},CASES)
        self.assertFalse(result["pass"])
        self.assertEqual(set(result["quality_regressions"]),{"greeting","cat"})
    def test_unreviewed_case_fails_closed(self):
        self.assertFalse(response_quality("こんにちは。",{"id":"unreviewed"})["pass"])
if __name__=="__main__":unittest.main()
