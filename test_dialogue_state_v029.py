import unittest
from dialogue_state_v029 import dialogue_state,repeat_check

class DialogueStateTests(unittest.TestCase):
    def setUp(self):
        self.history=[("最近、小説にはまっています","そう。どんな本を読んでいるの?")]
    def test_short_reply_answering_previous_question(self):
        self.assertTrue(dialogue_state(self.history,"SFです")["user_answered"])
    def test_repeated_question_rejected(self):
        repeat,sim=repeat_check("SFです","そう。どんな本を読んでいるのですね",self.history)
        self.assertTrue(repeat)
        self.assertGreaterEqual(sim,.76)
    def test_new_content_not_repetition(self):
        self.assertFalse(repeat_check("SFです","SF小説には宇宙探査を扱う作品があります。",self.history)[0])
    def test_empty_history(self):
        self.assertFalse(repeat_check("SFです","そう。どんな本を読んでいるの?",[])[0])
    def test_unrelated_question_does_not_trigger(self):
        self.assertFalse(repeat_check("あなたは誰ですか","そう。どんな本を読んでいるの?",self.history)[0])
if __name__=="__main__": unittest.main()
