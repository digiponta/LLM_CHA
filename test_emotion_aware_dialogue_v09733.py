import unittest
from emotion_aware_dialogue_v09733 import detect,EmotionDialogue

class EmotionAwareTests(unittest.TestCase):
    def test_joy_and_enjoyment(self):
        self.assertEqual(detect("合格した").primary,"JOY")
        self.assertEqual(detect("今日は楽しかった").primary,"ENJOYMENT")
        self.assertIn("良かった",detect("今日は楽しかった").response)
    def test_anger_and_sadness(self):
        self.assertEqual(detect("理不尽な対応だった").primary,"ANGER")
        self.assertEqual(detect("悲しかった").primary,"SADNESS")
    def test_negation(self):
        self.assertEqual(detect("楽しくなかった").primary,"DISAPPOINTMENT")
        self.assertEqual(detect("悲しくないよ").primary,"NON_SADNESS")
        self.assertNotIn("つらかった",detect("悲しくないよ").response)
    def test_mixed(self):
        result=detect("楽しかったけど疲れた")
        self.assertEqual(result.primary,"MIXED")
        self.assertEqual(set(result.secondary),{"ENJOYMENT","FATIGUE"})
    def test_greeting(self):
        x=detect("こんにちは")
        self.assertEqual(x.dialogue_act,"GREETING")
        self.assertIn("こんにちは",x.response)
    def test_abstain(self):
        self.assertIsNone(detect("あなたは誰ですか"))
        self.assertIsNone(detect("楽しかった？"))
        self.assertIsNone(detect(""))
        self.assertIsNone(detect("/sleep"))
    def test_ephemeral(self):
        state=EmotionDialogue()
        self.assertIsNotNone(state.respond("今日は楽しかった"))
        snap=state.snapshot()
        self.assertFalse(snap["train_ready"])
        self.assertFalse(snap["persisted"])
        self.assertEqual(snap["primary"],"ENJOYMENT")
        state.reset()
        self.assertEqual(state.snapshot()["status"],"NO_CONFIDENT_EMOTION")
if __name__=="__main__":unittest.main()
