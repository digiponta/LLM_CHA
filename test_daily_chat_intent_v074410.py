import unittest
from daily_chat_intent_v074410 import chat_reply

class DailyChatTests(unittest.TestCase):
    def test_like(self):
        self.assertEqual(chat_reply("猫は好き？",None)["intent"],"PREFERENCE_QUESTION")
    def test_cute(self):
        self.assertEqual(chat_reply("ぬこ、かわいいね",None)["intent"],"EMPATHY")
    def test_no_unsupported_extrapolation(self):
        self.assertIsNone(chat_reply("犬の飼育方法",None))
    def test_command(self):
        self.assertIsNone(chat_reply("/sleep",None))
    def test_no_learning(self):
        self.assertFalse(chat_reply("ぬこ、かわいいね",None)["train_ready"])

if __name__=="__main__":
    unittest.main()
