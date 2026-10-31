import unittest
from response_quality_guard_v013588282 import assess

class ResponseQualityGuardTests(unittest.TestCase):
    def test_reported_bad_answer_rejected(self):
        result=assess("。よれにする言語である六階層のシステム。",0.057,0.35)
        self.assertFalse(result["accepted"])
        self.assertEqual(result["reason"],"MALFORMED_LEADING_PUNCTUATION_LOW_AGREEMENT")
    def test_low_agreement_alone_preserves_good_answer(self):
        self.assertTrue(assess("閃亜鉛鉱は、亜鉛の硫化鉱物である。",0.057,0.35)["accepted"])
    def test_high_agreement_preserves_output(self):
        self.assertTrue(assess("。引用された文面です。",0.40,0.35)["accepted"])
    def test_prior_rejection_stays_rejected(self):
        self.assertFalse(assess("正しい文。",0.9,0.35,accepted=False)["accepted"])
    def test_empty_rejected(self):
        self.assertFalse(assess("",0.9,0.35)["accepted"])
    def test_nonanswer_not_special_cased(self):
        self.assertTrue(assess("今日は実験結果を確認しています。",0.057,0.35)["accepted"])
if __name__=="__main__":unittest.main()
