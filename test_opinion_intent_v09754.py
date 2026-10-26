import unittest
from opinion_intent_v09754 import detect
from definition_intent_v09752 import resolve
from incomplete_utterance_v09753 import detect as incomplete

class OpinionTests(unittest.TestCase):
    def test_positive(self):
        p=detect("満足は大切")
        self.assertEqual((p.intent,p.response),("OPINION","そう。"))
    def test_important(self):
        self.assertEqual(detect("健康は重要").response,"そう。")
    def test_necessary(self):
        self.assertEqual(detect("運動は必要").response,"そう。")
    def test_negative(self):
        p=detect("満足は大切ではない")
        self.assertTrue(p.negated)
        self.assertEqual(p.response,"そう。")
    def test_no_agreement_or_learning(self):
        p=detect("健康は重要")
        self.assertEqual(p.truth_state,"USER_OPINION_UNVERIFIED")
        self.assertFalse(p.train_ready or p.auto_promote or p.persisted)
    def test_definition_excluded(self):
        self.assertIsNone(detect("満足とは"))
        self.assertIsNotNone(resolve("満足とは"))
    def test_incomplete_excluded(self):
        self.assertIsNone(detect("満足は"))
        self.assertIsNotNone(incomplete("満足は"))
    def test_question_excluded(self):
        self.assertIsNone(detect("健康は重要ですか？"))
    def test_fact_excluded(self):
        self.assertIsNone(detect("地球は太陽の周りを回る"))
    def test_compound_excluded(self):
        self.assertIsNone(detect("満足は大切だけど健康も重要"))
if __name__=="__main__":unittest.main()
