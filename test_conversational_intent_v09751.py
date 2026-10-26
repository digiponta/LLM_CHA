import unittest
from conversational_intent_v09751 import detect
from definition_search_priority_v09751 import is_definition_query,clipboard_allowed,daily_allowed
class ConversationalIntentTests(unittest.TestCase):
    def test_short_positive(self):
        self.assertEqual(detect("満足").intent,"SATISFACTION")
    def test_short_negative(self):
        self.assertEqual(detect("いまいち").intent,"NEGATIVE_EVALUATION")
    def test_mixed(self):
        self.assertEqual(detect("微妙だった").intent,"MIXED_EVALUATION")
    def test_action(self):
        p=detect("ケーキを食べた")
        self.assertEqual((p.intent,p.action,p.object),("DAILY_ACTION","EAT","ケーキ"))
    def test_negative_action(self):
        p=detect("コーヒーを飲まなかった")
        self.assertEqual(p.action,"DRINK")
        self.assertTrue(p.negated)
    def test_bare_action(self):
        self.assertEqual(detect("買った").action,"BUY")
    def test_toha_is_search(self):
        for s in ("満足とは","食べたとは何か","好きとは","量子力学とは"):
            self.assertTrue(is_definition_query(s))
            self.assertFalse(clipboard_allowed(s))
            self.assertFalse(daily_allowed(s))
            self.assertIsNone(detect(s))
    def test_ordinary_daily_allowed(self):
        self.assertTrue(clipboard_allowed("満足"))
        self.assertTrue(daily_allowed("ケーキを食べた"))
    def test_questions_not_daily(self):
        self.assertIsNone(detect("ケーキを食べた？"))
    def test_no_promotion(self):
        p=detect("食べた")
        self.assertFalse(p.train_ready or p.auto_promote or p.persisted)
if __name__=="__main__":unittest.main()
