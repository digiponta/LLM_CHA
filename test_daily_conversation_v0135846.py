"""Independent checks for v0.13.58.46 narrow conversational routing."""
import unittest
from daily_conversation_v0135846 import classify,route
class DailyConversationTests(unittest.TestCase):
    def test_optin_off(self):
        self.assertIsNone(route("こんにちは",{}))
    def test_greetings(self):
        self.assertEqual(route("こんにちは",{"LLM_CHA_DAILY_RUNTIME":"1"}).intent,"greeting")
        self.assertEqual(classify("おはようございます").intent,"greeting")
    def test_feelings(self):
        self.assertEqual(classify("今日は疲れた").intent,"feeling_tired")
        self.assertEqual(classify("少し眠い").intent,"feeling_tired")
        self.assertEqual(classify("今日はいい気分").intent,"feeling_good")
    def test_thanks_and_invite(self):
        self.assertEqual(classify("ありがとう").intent,"thanks")
        self.assertEqual(classify("少し話さない？").intent,"casual_invite")
    def test_factual_and_command_do_not_intercept(self):
        for q in ("CPUとは","量子力学とは","吾輩は猫であるの作者は","/sleep status","今日は疲れた理由は？","こんにちは。量子力学とは"):
            with self.subTest(q=q):self.assertIsNone(classify(q))
    def test_ambiguous_or_long_not_intercepted(self):
        self.assertIsNone(classify(" "))
        self.assertIsNone(classify("あ"*81))
if __name__=="__main__":unittest.main()
