import unittest
from preference_intent_v09750 import detect
from chat_window_v061 import build_chat_command
class PreferenceIntentTests(unittest.TestCase):
    def test_like(self):
        p=detect("ハム&ゴーダチーズ スターバックス バゲットサンドも好き")
        self.assertEqual(p.object,"ハム&ゴーダチーズ スターバックス バゲットサンド")
        self.assertEqual(p.predicate,"LIKE")
        self.assertIn("も好き",p.response)
    def test_dislike(self):
        p=detect("コーヒーが嫌い")
        self.assertIsNotNone(p)
        self.assertEqual(p.polarity,"NEGATIVE")
    def test_question_not_routed(self):
        self.assertIsNone(detect("コーヒーは好きですか？"))
    def test_unclear_not_routed(self):
        self.assertIsNone(detect("ハムは好きだけどケーキは嫌い"))
    def test_no_promote(self):
        p=detect("ラテが好き")
        self.assertFalse(p.train_ready or p.auto_promote or p.persisted)
    def test_gui_option_not_forwarded(self):
        command,_=build_chat_command(["--gui-only-input","--final-guard"])
        self.assertNotIn("--gui-only-input",command)
        self.assertIn("--final-guard",command)
if __name__=="__main__":unittest.main()
