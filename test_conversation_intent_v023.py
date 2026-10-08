import unittest
from character_profile_v010 import CharacterProfile
from conversation_intent_v023 import intent_reply

P=CharacterProfile("nagato","長門有希","寡黙","簡潔")

class IntentTests(unittest.TestCase):
    def test_identity_paraphrases(self):
        for q in ["お名前を伺えますか","自分が何者か説明して","あなたは誰ですか","自己紹介してください"]:
            self.assertEqual(intent_reply(q,P,[]),("identity","長門有希。"))
    def test_opt_in(self):
        self.assertIsNone(intent_reply("お名前を伺えますか",None,[]))
    def test_gratitude(self):
        self.assertEqual(intent_reply("助かりました",P,[])[0],"acknowledgement")
    def test_fatigue(self):
        self.assertEqual(intent_reply("今日はくたくたです",P,[])[0],"feeling")
    def test_invite(self):
        self.assertEqual(intent_reply("少しおしゃべりしませんか",P,[])[0],"casual")
    def test_context(self):
        self.assertEqual(intent_reply("その本は面白かった？",P,[("昨日は科学の本を読んだ","そう。")])[0],"book_context")
        self.assertIsNone(intent_reply("その本は面白かった？",P,[]))
    def test_factual_queries_pass_through(self):
        for q in ["CPUとは","GPUの並列処理が速い理由を説明して","量子力学とは","GPUが疲れる理由"]:
            self.assertIsNone(intent_reply(q,P,[]))
if __name__=="__main__":unittest.main()
